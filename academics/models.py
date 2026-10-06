from django.conf import settings
from django.db import models


class Course(models.Model):
    course_code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=150)
    unit = models.PositiveSmallIntegerField(default=3)
    level = models.CharField(max_length=3, default='100')

    class Meta:
        ordering = ['course_code']

    def __str__(self):
        return f'{self.course_code} - {self.title}'


class LecturerCourse(models.Model):
    """Which lecturer is allowed to upload results for which course."""

    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_courses',
        limit_choices_to={'role': 'lecturer'},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assigned_lecturers')

    class Meta:
        unique_together = ('lecturer', 'course')

    def __str__(self):
        return f'{self.lecturer} -> {self.course}'


class Result(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='results',
        limit_choices_to={'role': 'student'},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.CharField(max_length=10, choices=[('first', 'First'), ('second', 'Second')])
    session = models.CharField(max_length=9, help_text='e.g. 2025/2026')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='results_uploaded',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='results_approved',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'semester', 'session')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} - {self.course} - {self.score}'

    @property
    def grade(self):
        score = float(self.score)
        if score >= 70:
            return 'A'
        if score >= 60:
            return 'B'
        if score >= 50:
            return 'C'
        if score >= 45:
            return 'D'
        return 'F'
