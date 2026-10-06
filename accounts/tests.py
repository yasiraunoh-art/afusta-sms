from django.test import TestCase
from django.urls import reverse

from academics.models import Course, LecturerCourse

from .models import LecturerProfile, StudentProfile, User


def make_student(username='CSC/2021/001', password='student12345'):
    user = User.objects.create_user(
        username=username, password=password, email='stu@afusta.edu.ng',
        first_name='Amina', last_name='Yusuf', phone='+2348022222222', role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=user, matric_no=username, level='300')
    return user


def make_lecturer(username='CSC-LEC-01', password='lecturer12345'):
    user = User.objects.create_user(
        username=username, password=password, email='lec@afusta.edu.ng',
        first_name='Musa', last_name='Bello', phone='+2348011111111', role=User.Role.LECTURER,
    )
    LecturerProfile.objects.create(user=user, staff_id=username)
    return user


class HomePageTests(TestCase):
    """The sign-up / log-in calls to action only belong to signed-out visitors."""

    def test_signed_out_visitor_sees_both_calls_to_action(self):
        response = self.client.get('/')
        self.assertContains(response, 'Register as a student')
        self.assertContains(response, 'Staff / admin log in')
        self.assertNotContains(response, 'Go to my dashboard')

    def test_signed_in_user_sees_a_dashboard_link_instead(self):
        self.client.force_login(make_student())
        response = self.client.get('/')
        self.assertContains(response, 'Go to my dashboard')
        self.assertNotContains(response, 'Register as a student')
        self.assertNotContains(response, 'Staff / admin log in')


class UserMenuTests(TestCase):
    """Every signed-in role gets the same top-right menu."""

    def test_menu_offers_settings_and_sign_out(self):
        for user in [make_student(), make_lecturer()]:
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse('accounts:redirect_after_login'), follow=True)
                self.assertContains(response, reverse('accounts:settings'))
                self.assertContains(response, reverse('accounts:logout'))
                self.assertContains(response, 'Sign out')
                self.assertContains(response, user.get_full_name())

    def test_avatar_uses_initials(self):
        self.client.force_login(make_student())
        response = self.client.get(reverse('academics:student_dashboard'))
        self.assertContains(response, '>AY<')

    def test_initials_fall_back_to_the_username(self):
        user = User.objects.create_user(
            username='admin', password='pw', phone='+234', role=User.Role.ADMIN)
        self.assertEqual(user.initials, 'AD')


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.client.force_login(self.student)
        self.url = reverse('accounts:settings')

    def test_page_shows_profile_and_password_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change password')
        self.assertContains(response, 'CSC/2021/001')
        self.assertContains(response, 'Matric no.')

    def test_lecturer_sees_staff_id_label(self):
        self.client.force_login(make_lecturer())
        self.assertContains(self.client.get(self.url), 'Staff ID')

    def test_password_change_works_and_keeps_the_session(self):
        response = self.client.post(self.url, {
            'old_password': 'student12345',
            'new_password1': 'a-much-better-password',
            'new_password2': 'a-much-better-password',
        }, follow=True)
        self.assertContains(response, 'Your password has been changed.')

        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('a-much-better-password'))
        # update_session_auth_hash means we should still be signed in.
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_wrong_old_password_is_rejected(self):
        response = self.client.post(self.url, {
            'old_password': 'not-my-password',
            'new_password1': 'a-much-better-password',
            'new_password2': 'a-much-better-password',
        })
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('student12345'))

    def test_mismatched_new_passwords_are_rejected(self):
        self.client.post(self.url, {
            'old_password': 'student12345',
            'new_password1': 'a-much-better-password',
            'new_password2': 'a-different-password',
        })
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('student12345'))

    def test_signed_out_visitors_are_sent_to_the_login_page(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)


class RolePageRenderTests(TestCase):
    """The student and lecturer pages render with their own sidebar nav."""

    def test_student_pages(self):
        self.client.force_login(make_student())
        response = self.client.get(reverse('academics:student_dashboard'))
        self.assertContains(response, 'My results')
        self.assertNotContains(response, 'Pending approvals')  # admin-only nav

    def test_lecturer_pages(self):
        lecturer = make_lecturer()
        course = Course.objects.create(course_code='CSC301', title='Operating Systems', level='300')
        LecturerCourse.objects.create(lecturer=lecturer, course=course)
        self.client.force_login(lecturer)

        for name in ['academics:lecturer_dashboard', 'academics:upload_result',
                     'academics:bulk_upload_results', 'accounts:settings']:
            with self.subTest(view=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Bulk upload (CSV)')  # lecturer nav rendered

    def test_settings_page_falls_back_to_the_role_nav(self):
        """settings.html doesn't define a sidenav block, so base_app picks one."""
        self.client.force_login(make_student())
        self.assertContains(self.client.get(reverse('accounts:settings')), 'My results')

        self.client.force_login(make_lecturer())
        self.assertContains(self.client.get(reverse('accounts:settings')), 'Upload a result')
