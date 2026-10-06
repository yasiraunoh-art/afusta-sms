from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import LecturerForm, StudentForm, StyledPasswordChangeForm
from .models import User


@login_required
def redirect_after_login(request):
    role = request.user.role
    if role == User.Role.STUDENT:
        return redirect('academics:student_dashboard')
    if role == User.Role.LECTURER:
        return redirect('academics:lecturer_dashboard')
    return redirect('academics:admin_dashboard')


def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account is ready.')
            return redirect('academics:student_dashboard')
    else:
        form = StudentForm()
    return render(request, 'accounts/register_student.html', {'form': form})


@login_required
def account_settings(request):
    """Every role's own settings page. Currently: change your password."""
    if request.method == 'POST':
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Changing the password rotates the session hash, so without this
            # the user would be logged straight back out.
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed.')
            return redirect('accounts:settings')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = StyledPasswordChangeForm(request.user)
    return render(request, 'accounts/settings.html', {'form': form})


@role_required('admin')
def create_lecturer(request):
    if request.method == 'POST':
        form = LecturerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lecturer account created.')
            return redirect('academics:manage_lecturers')
    else:
        form = LecturerForm()
    return render(request, 'accounts/create_lecturer.html', {'form': form})
