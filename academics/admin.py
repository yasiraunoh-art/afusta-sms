from django.contrib import admin

from .models import Course, LecturerCourse, Result

admin.site.register(Course)
admin.site.register(LecturerCourse)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'score', 'status', 'semester', 'session', 'created_at')
    list_filter = ('status', 'semester', 'session', 'course')
