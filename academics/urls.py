from django.urls import path

from . import views

app_name = 'academics'

urlpatterns = [
    # student
    path('student/', views.student_dashboard, name='student_dashboard'),

    # lecturer
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/upload/', views.upload_result, name='upload_result'),
    path('lecturer/bulk-upload/', views.bulk_upload_results, name='bulk_upload_results'),

    # admin
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/pending/', views.pending_results, name='pending_results'),
    path('admin-portal/pending/<int:pk>/approve/', views.approve_result, name='approve_result'),
    path('admin-portal/pending/<int:pk>/reject/', views.reject_result, name='reject_result'),
    path('admin-portal/courses/', views.manage_courses, name='manage_courses'),
    path('admin-portal/courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('admin-portal/courses/<int:pk>/delete/', views.delete_course, name='delete_course'),

    path('admin-portal/assign-lecturer/', views.assign_lecturer, name='assign_lecturer'),

    path('admin-portal/students/', views.manage_students, name='manage_students'),
    path('admin-portal/students/new/', views.add_student, name='add_student'),
    path('admin-portal/students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('admin-portal/students/<int:pk>/delete/', views.delete_student, name='delete_student'),

    path('admin-portal/lecturers/', views.manage_lecturers, name='manage_lecturers'),
    path('admin-portal/lecturers/<int:pk>/edit/', views.edit_lecturer, name='edit_lecturer'),
    path('admin-portal/lecturers/<int:pk>/delete/', views.delete_lecturer, name='delete_lecturer'),

    path('admin-portal/notifications/', views.notification_log, name='notification_log'),
]
