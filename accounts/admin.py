from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LecturerProfile, StudentProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (('Result alert fields', {'fields': ('role', 'phone')}),)


admin.site.register(StudentProfile)
admin.site.register(LecturerProfile)
