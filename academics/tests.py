from django.test import TestCase
from django.urls import reverse

from accounts.models import LecturerProfile, StudentProfile, User

from .models import Course, LecturerCourse, Result


class AdminTestCase(TestCase):
    """One admin, one lecturer, one student and one course, all logged in as admin."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pw', email='admin@afusta.edu.ng',
            phone='+2348000000000', role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

        self.course = Course.objects.create(course_code='CSC301', title='Operating Systems', level='300')

        self.lecturer = User.objects.create_user(
            username='CSC-LEC-01', password='pw', email='lec@afusta.edu.ng',
            first_name='Musa', last_name='Bello', phone='+2348011111111', role=User.Role.LECTURER,
        )
        LecturerProfile.objects.create(user=self.lecturer, staff_id='CSC-LEC-01')

        self.student = User.objects.create_user(
            username='CSC/2021/001', password='pw', email='stu@afusta.edu.ng',
            first_name='Amina', last_name='Yusuf', phone='+2348022222222', role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(user=self.student, matric_no='CSC/2021/001', level='300')


class AdminPageRenderTests(AdminTestCase):
    """Every admin page renders, and the shared sidebar include works."""

    def test_every_admin_page_renders(self):
        for name, args in [
            ('academics:admin_dashboard', []),
            ('academics:pending_results', []),
            ('academics:manage_courses', []),
            ('academics:assign_lecturer', []),
            ('academics:manage_lecturers', []),
            ('academics:manage_students', []),
            ('academics:notification_log', []),
            ('accounts:create_lecturer', []),
            ('academics:add_student', []),
            ('academics:edit_course', [self.course.pk]),
            ('academics:delete_course', [self.course.pk]),
            ('academics:edit_student', [self.student.pk]),
            ('academics:delete_student', [self.student.pk]),
            ('academics:edit_lecturer', [self.lecturer.pk]),
            ('academics:delete_lecturer', [self.lecturer.pk]),
        ]:
            with self.subTest(view=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Notification log')  # the sidebar include rendered

    def test_sidebar_highlights_the_current_page(self):
        response = self.client.get(reverse('academics:manage_students'))
        self.assertContains(response, 'class="side-link active" href="/admin-portal/students/"')
        self.assertContains(response, 'class="side-link" href="/admin-portal/courses/"')

    def test_edit_form_is_prefilled(self):
        response = self.client.get(reverse('academics:edit_student', args=[self.student.pk]))
        self.assertContains(response, 'value="CSC/2021/001"')
        self.assertContains(response, 'Leave blank to keep the current password.')


class AdminManagementTests(AdminTestCase):
    """Covers the admin's add/edit/delete pages for courses, students and lecturers."""

    # -- courses ---------------------------------------------------------- #

    def test_add_course(self):
        self.client.post(reverse('academics:manage_courses'), {
            'course_code': 'CSC302', 'title': 'Databases', 'unit': 3, 'level': '300',
        })
        self.assertTrue(Course.objects.filter(course_code='CSC302').exists())

    def test_edit_course(self):
        self.client.post(reverse('academics:edit_course', args=[self.course.pk]), {
            'course_code': 'CSC301', 'title': 'Operating Systems II', 'unit': 4, 'level': '300',
        })
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Operating Systems II')
        self.assertEqual(self.course.unit, 4)

    def test_delete_course_confirms_before_deleting(self):
        url = reverse('academics:delete_course', args=[self.course.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

        self.client.post(url)
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())

    # -- students --------------------------------------------------------- #

    def test_add_student(self):
        self.client.post(reverse('academics:add_student'), {
            'first_name': 'Zainab', 'last_name': 'Sani', 'matric_no': 'csc/2021/002',
            'level': '200', 'email': 'z@afusta.edu.ng', 'phone': '+2348033333333',
            'password': 'student12345',
        })
        user = User.objects.get(username='CSC/2021/002')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(user.student_profile.level, '200')
        self.assertTrue(user.check_password('student12345'))

    def test_edit_student_keeps_password_when_blank(self):
        self.client.post(reverse('academics:edit_student', args=[self.student.pk]), {
            'first_name': 'Amina', 'last_name': 'Yusuf', 'matric_no': 'CSC/2021/001',
            'level': '400', 'email': 'new@afusta.edu.ng', 'phone': '+2348022222222',
            'password': '',
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.email, 'new@afusta.edu.ng')
        self.assertEqual(self.student.student_profile.level, '400')
        self.assertTrue(self.student.check_password('pw'))

    def test_edit_student_changes_password_when_given(self):
        self.client.post(reverse('academics:edit_student', args=[self.student.pk]), {
            'first_name': 'Amina', 'last_name': 'Yusuf', 'matric_no': 'CSC/2021/001',
            'level': '300', 'email': 'stu@afusta.edu.ng', 'phone': '+2348022222222',
            'password': 'brand-new-pw',
        })
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('brand-new-pw'))

    def test_changing_matric_no_moves_the_login(self):
        self.client.post(reverse('academics:edit_student', args=[self.student.pk]), {
            'first_name': 'Amina', 'last_name': 'Yusuf', 'matric_no': 'CSC/2021/999',
            'level': '300', 'email': 'stu@afusta.edu.ng', 'phone': '+2348022222222',
            'password': '',
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.username, 'CSC/2021/999')
        self.assertEqual(self.student.student_profile.matric_no, 'CSC/2021/999')

    def test_cannot_reuse_another_students_matric_no(self):
        other = User.objects.create_user(
            username='CSC/2021/003', password='pw', phone='+234', role=User.Role.STUDENT)
        StudentProfile.objects.create(user=other, matric_no='CSC/2021/003')

        response = self.client.post(reverse('academics:edit_student', args=[self.student.pk]), {
            'first_name': 'Amina', 'last_name': 'Yusuf', 'matric_no': 'CSC/2021/003',
            'level': '300', 'email': 'stu@afusta.edu.ng', 'phone': '+2348022222222',
            'password': '',
        })
        self.assertContains(response, 'already exists')
        self.student.refresh_from_db()
        self.assertEqual(self.student.username, 'CSC/2021/001')

    def test_delete_student_takes_their_results_with_them(self):
        Result.objects.create(
            student=self.student, course=self.course, score=70,
            semester='first', session='2025/2026', uploaded_by=self.lecturer,
        )
        self.client.post(reverse('academics:delete_student', args=[self.student.pk]))
        self.assertFalse(User.objects.filter(pk=self.student.pk).exists())
        self.assertEqual(Result.objects.count(), 0)

    # -- lecturers -------------------------------------------------------- #

    def test_edit_lecturer(self):
        self.client.post(reverse('academics:edit_lecturer', args=[self.lecturer.pk]), {
            'first_name': 'Musa', 'last_name': 'Bello', 'staff_id': 'CSC-LEC-09',
            'email': 'musa@afusta.edu.ng', 'phone': '+2348011111111', 'password': '',
        })
        self.lecturer.refresh_from_db()
        self.assertEqual(self.lecturer.username, 'CSC-LEC-09')
        self.assertEqual(self.lecturer.lecturer_profile.staff_id, 'CSC-LEC-09')

    def test_delete_lecturer_keeps_results_but_drops_assignments(self):
        LecturerCourse.objects.create(lecturer=self.lecturer, course=self.course)
        Result.objects.create(
            student=self.student, course=self.course, score=70,
            semester='first', session='2025/2026', uploaded_by=self.lecturer,
        )
        self.client.post(reverse('academics:delete_lecturer', args=[self.lecturer.pk]))

        self.assertFalse(User.objects.filter(pk=self.lecturer.pk).exists())
        self.assertEqual(LecturerCourse.objects.count(), 0)
        result = Result.objects.get()
        self.assertIsNone(result.uploaded_by)

    # -- access control --------------------------------------------------- #

    def test_non_admin_is_turned_away(self):
        self.client.force_login(self.lecturer)
        for name, args in [
            ('academics:add_student', []),
            ('academics:edit_student', [self.student.pk]),
            ('academics:delete_student', [self.student.pk]),
            ('academics:edit_course', [self.course.pk]),
            ('academics:delete_course', [self.course.pk]),
            ('academics:edit_lecturer', [self.lecturer.pk]),
            ('academics:delete_lecturer', [self.lecturer.pk]),
        ]:
            with self.subTest(view=name):
                response = self.client.get(reverse(name, args=args))
                self.assertRedirects(response, reverse('accounts:redirect_after_login'),
                                     target_status_code=302)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())
