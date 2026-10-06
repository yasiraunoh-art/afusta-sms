import csv
import io

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.forms import LecturerForm, StudentForm
from accounts.models import User
from notifications.models import NotificationLog
from notifications.services import send_result_alert
from notifications.tasks import send_result_alert_task

from .forms import AssignLecturerForm, CourseForm, ResultUploadForm
from .models import Course, LecturerCourse, Result


# ---------------------------------------------------------------------- #
# Student
# ---------------------------------------------------------------------- #

@role_required('student')
def student_dashboard(request):
    results = Result.objects.filter(
        student=request.user, status=Result.Status.APPROVED
    ).select_related('course')
    return render(request, 'academics/student_dashboard.html', {'results': results})


# ---------------------------------------------------------------------- #
# Lecturer
# ---------------------------------------------------------------------- #

@role_required('lecturer')
def lecturer_dashboard(request):
    courses = Course.objects.filter(assigned_lecturers__lecturer=request.user)
    results = Result.objects.filter(uploaded_by=request.user).select_related('student', 'course')
    return render(request, 'academics/lecturer_dashboard.html', {'courses': courses, 'results': results})


@role_required('lecturer')
def upload_result(request):
    if request.method == 'POST':
        form = ResultUploadForm(request.POST, lecturer=request.user)
        if form.is_valid():
            result = form.save(commit=False)
            result.uploaded_by = request.user
            result.save()
            messages.success(request, 'Result submitted and awaiting admin approval.')
            return redirect('academics:lecturer_dashboard')
    else:
        form = ResultUploadForm(lecturer=request.user)
    return render(request, 'academics/upload_result.html', {'form': form})


@role_required('lecturer')
def bulk_upload_results(request):
    """CSV columns: matric_no,course_code,score,semester,session"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        allowed_courses = set(
            LecturerCourse.objects.filter(lecturer=request.user).values_list('course__course_code', flat=True)
        )
        raw = request.FILES['csv_file'].read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(raw))
        created, skipped = 0, 0
        for row in reader:
            course_code = row.get('course_code', '').strip().upper()
            matric_no = row.get('matric_no', '').strip().upper()
            if course_code not in allowed_courses:
                skipped += 1
                continue
            student = User.objects.filter(role=User.Role.STUDENT, student_profile__matric_no=matric_no).first()
            course = Course.objects.filter(course_code=course_code).first()
            if not student or not course:
                skipped += 1
                continue
            Result.objects.update_or_create(
                student=student, course=course,
                semester=row.get('semester', 'first').strip().lower(),
                session=row.get('session', '').strip(),
                defaults={'score': row.get('score', 0), 'uploaded_by': request.user, 'status': Result.Status.PENDING},
            )
            created += 1
        messages.success(request, f'{created} result(s) submitted, {skipped} row(s) skipped.')
        return redirect('academics:lecturer_dashboard')
    return render(request, 'academics/bulk_upload.html')


# ---------------------------------------------------------------------- #
# Admin
# ---------------------------------------------------------------------- #

@role_required('admin')
def admin_dashboard(request):
    context = {
        'pending_count': Result.objects.filter(status=Result.Status.PENDING).count(),
        'approved_count': Result.objects.filter(status=Result.Status.APPROVED).count(),
        'student_count': User.objects.filter(role=User.Role.STUDENT).count(),
        'lecturer_count': User.objects.filter(role=User.Role.LECTURER).count(),
        'course_count': Course.objects.count(),
    }
    return render(request, 'academics/admin_dashboard.html', context)


@role_required('admin')
def pending_results(request):
    results = Result.objects.filter(status=Result.Status.PENDING).select_related('student', 'course')
    return render(request, 'academics/pending_results.html', {'results': results})


@role_required('admin')
def approve_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    result.status = Result.Status.APPROVED
    result.approved_by = request.user
    result.approved_at = timezone.now()
    result.save()
    if settings.NOTIFY_SYNCHRONOUSLY:
        send_result_alert(result)
    else:
        send_result_alert_task.delay(result.id)
    messages.success(request, f"Result for {result.student} approved and alerts dispatched.")
    return redirect('academics:pending_results')


@role_required('admin')
def reject_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    result.status = Result.Status.REJECTED
    result.save()
    messages.info(request, f'Result for {result.student} rejected and sent back to the lecturer.')
    return redirect('academics:pending_results')


def _confirm_delete(request, obj, *, label, back_to, warning=''):
    """Shared delete flow: confirm on GET, actually delete on POST.

    Everything deletable here cascades into results or assignments, so the
    confirmation page spells out what else goes with it.
    """
    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'{label} deleted.')
        return redirect(back_to)
    return render(request, 'academics/confirm_delete.html', {
        'label': label, 'warning': warning, 'back_to': back_to,
    })


@role_required('admin')
def manage_courses(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added.')
            return redirect('academics:manage_courses')
    else:
        form = CourseForm()
    return render(request, 'academics/manage_courses.html', {
        'form': form, 'courses': Course.objects.all(),
    })


@role_required('admin')
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'{course.course_code} updated.')
            return redirect('academics:manage_courses')
    else:
        form = CourseForm(instance=course)
    return render(request, 'academics/course_form.html', {'form': form, 'course': course})


@role_required('admin')
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return _confirm_delete(
        request, course,
        label=f'{course.course_code} — {course.title}',
        back_to='academics:manage_courses',
        warning=(
            f'{course.results.count()} result(s) and '
            f'{course.assigned_lecturers.count()} lecturer assignment(s) will be deleted with it.'
        ),
    )


@role_required('admin')
def assign_lecturer(request):
    if request.method == 'POST':
        form = AssignLecturerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lecturer assigned to course.')
            return redirect('academics:assign_lecturer')
    else:
        form = AssignLecturerForm()
    return render(request, 'academics/assign_lecturer.html', {
        'form': form, 'assignments': LecturerCourse.objects.select_related('lecturer', 'course'),
    })


@role_required('admin')
def manage_students(request):
    students = User.objects.filter(role=User.Role.STUDENT).select_related('student_profile')
    return render(request, 'academics/manage_students.html', {'students': students})


@role_required('admin')
def add_student(request):
    """Admins can enrol a student directly, as well as students self-registering."""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student account created.')
            return redirect('academics:manage_students')
    else:
        form = StudentForm()
    return render(request, 'academics/student_form.html', {'form': form})


@role_required('admin')
def edit_student(request, pk):
    student = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'{student.get_full_name()} updated.')
            return redirect('academics:manage_students')
    else:
        form = StudentForm(instance=student)
    return render(request, 'academics/student_form.html', {'form': form, 'student': student})


@role_required('admin')
def delete_student(request, pk):
    student = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)
    return _confirm_delete(
        request, student,
        label=f'{student.get_full_name()} ({student.student_profile.matric_no})',
        back_to='academics:manage_students',
        warning=f'Their {student.results.count()} result(s) and alert history will be deleted too.',
    )


@role_required('admin')
def manage_lecturers(request):
    lecturers = User.objects.filter(role=User.Role.LECTURER).select_related('lecturer_profile')
    return render(request, 'academics/manage_lecturers.html', {'lecturers': lecturers})


@role_required('admin')
def edit_lecturer(request, pk):
    lecturer = get_object_or_404(User, pk=pk, role=User.Role.LECTURER)
    if request.method == 'POST':
        form = LecturerForm(request.POST, instance=lecturer)
        if form.is_valid():
            form.save()
            messages.success(request, f'{lecturer.get_full_name()} updated.')
            return redirect('academics:manage_lecturers')
    else:
        form = LecturerForm(instance=lecturer)
    return render(request, 'academics/lecturer_form.html', {'form': form, 'lecturer': lecturer})


@role_required('admin')
def delete_lecturer(request, pk):
    lecturer = get_object_or_404(User, pk=pk, role=User.Role.LECTURER)
    return _confirm_delete(
        request, lecturer,
        label=f'{lecturer.get_full_name()} ({lecturer.lecturer_profile.staff_id})',
        back_to='academics:manage_lecturers',
        warning=(
            f'{lecturer.assigned_courses.count()} course assignment(s) will be removed. '
            'Results they uploaded stay, but will no longer show an uploader.'
        ),
    )


@role_required('admin')
def notification_log(request):
    logs = NotificationLog.objects.select_related('result__student', 'result__course')[:200]
    return render(request, 'academics/notification_log.html', {'logs': logs})
