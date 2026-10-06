from django import forms

from accounts.models import User

from .models import Course, LecturerCourse, Result


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'title', 'unit', 'level']
        widgets = {
            'course_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CSC 301'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.NumberInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('100', '100 Level'), ('200', '200 Level'), ('300', '300 Level'), ('400', '400 Level'),
            ]),
        }


class AssignLecturerForm(forms.ModelForm):
    class Meta:
        model = LecturerCourse
        fields = ['lecturer', 'course']
        widgets = {
            'lecturer': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lecturer'].queryset = User.objects.filter(role=User.Role.LECTURER)


class ResultUploadForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'course', 'score', 'semester', 'session']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.01'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025/2026'}),
        }

    def __init__(self, *args, lecturer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(role=User.Role.STUDENT)
        if lecturer is not None:
            course_ids = LecturerCourse.objects.filter(lecturer=lecturer).values_list('course_id', flat=True)
            self.fields['course'].queryset = Course.objects.filter(id__in=course_ids)
