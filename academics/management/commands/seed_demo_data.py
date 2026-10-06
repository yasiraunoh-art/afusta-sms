import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import LecturerProfile, StudentProfile, User
from academics.models import Course, LecturerCourse, Result


class Command(BaseCommand):
    help = 'Creates demo accounts, courses and a sample result for testing/demoing the system.'

    def handle(self, *args, **options):
        admin_password = os.environ.get('DEMO_ADMIN_PASSWORD')
        if not settings.DEBUG and not admin_password:
            raise CommandError(
                'Set DEMO_ADMIN_PASSWORD before seeding demo data with DEBUG disabled.'
            )

        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin', password=admin_password or 'admin12345', email='admin@afusta.edu.ng',
                first_name='Dept', last_name='Admin', phone='+2348000000000', role=User.Role.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS('Created admin login: admin'))
        else:
            admin = User.objects.get(username='admin')

        if not User.objects.filter(username='CSC-LEC-01').exists():
            lecturer = User.objects.create_user(
                username='CSC-LEC-01', password='lecturer12345', email='lecturer@afusta.edu.ng',
                first_name='Musa', last_name='Bello', phone='+2348011111111', role=User.Role.LECTURER,
            )
            LecturerProfile.objects.create(user=lecturer, staff_id='CSC-LEC-01')
            self.stdout.write(self.style.SUCCESS('Created lecturer login: CSC-LEC-01 / lecturer12345'))
        else:
            lecturer = User.objects.get(username='CSC-LEC-01')

        if not User.objects.filter(username='CSC/2021/001').exists():
            student = User.objects.create_user(
                username='CSC/2021/001', password='student12345', email='student@afusta.edu.ng',
                first_name='Amina', last_name='Yusuf', phone='+2348022222222', role=User.Role.STUDENT,
            )
            StudentProfile.objects.create(user=student, matric_no='CSC/2021/001', level='300')
            self.stdout.write(self.style.SUCCESS('Created student login: CSC/2021/001 / student12345'))
        else:
            student = User.objects.get(username='CSC/2021/001')

        course, _ = Course.objects.get_or_create(
            course_code='CSC301', defaults={'title': 'Operating Systems', 'unit': 3, 'level': '300'}
        )
        LecturerCourse.objects.get_or_create(lecturer=lecturer, course=course)

        Result.objects.get_or_create(
            student=student, course=course, semester='first', session='2025/2026',
            defaults={'score': 78, 'uploaded_by': lecturer, 'status': Result.Status.PENDING},
        )
        self.stdout.write(self.style.SUCCESS('Demo data ready. Log in as admin to approve the pending result.'))
