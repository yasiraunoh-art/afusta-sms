from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A single auth table for all three roles.

    Keeping one User model (instead of three separate login tables) means
    Django's built-in auth, permissions and admin all work unmodified.
    The role decides which dashboard a user is redirected to and which
    profile table holds their extra details.
    """

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        LECTURER = 'lecturer', 'Lecturer'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=10, choices=Role.choices)
    phone = models.CharField(
        max_length=20,
        help_text='Include country code where possible, e.g. +2348012345678',
    )

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    @property
    def initials(self):
        """One or two letters for the avatar in the top-right user menu."""
        letters = ''.join(part[0] for part in (self.first_name, self.last_name) if part)
        return (letters or self.username[:2]).upper()


class StudentProfile(models.Model):
    LEVELS = [('100', '100 Level'), ('200', '200 Level'), ('300', '300 Level'), ('400', '400 Level')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    matric_no = models.CharField(max_length=30, unique=True)
    level = models.CharField(max_length=3, choices=LEVELS, default='100')

    def __str__(self):
        return self.matric_no


class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.staff_id
