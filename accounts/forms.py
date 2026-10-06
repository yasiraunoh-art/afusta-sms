from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .models import LecturerProfile, StudentProfile, User


class StyledAuthenticationForm(AuthenticationForm):
    """Adds the project's input classes to the built-in login form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Matric no. / staff ID / username'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Password'}
        )


class StyledPasswordChangeForm(PasswordChangeForm):
    """Django's password change form, restyled for the account settings page.

    Django does the real work here: it checks the old password and runs the
    new one through AUTH_PASSWORD_VALIDATORS.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class AccountForm(forms.Form):
    """Base create/edit form for the two account types that have a profile.

    Pass `instance=<User>` to edit an existing account, or leave it out to
    create a new one. On create the password is required; on edit it is
    optional and only changes the password when it's actually filled in.

    Subclasses supply the ID field (matric no. / staff ID) that doubles as
    the login username, plus the profile model it lives on.
    """

    #: name of the subclass field holding the login ID, e.g. 'matric_no'
    id_field = None
    #: profile model the ID is stored on, e.g. StudentProfile
    profile_model = None
    #: role assigned to accounts created through this form
    role = None

    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+2348012345678'}),
    )
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            self.fields['password'].required = False
            self.fields['password'].label = 'New password'
            self.fields['password'].help_text = 'Leave blank to keep the current password.'
            self.initial = self.initial_for(instance)

    def initial_for(self, instance):
        """Field values to prefill when editing. Extended by subclasses."""
        return {
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
            'phone': instance.phone,
        }

    def clean_login_id(self, value):
        """Normalise an ID and reject it if another account already uses it.

        The ID is also the username, so it has to be unique across *all*
        accounts, not just the ones with this profile type.
        """
        value = value.strip().upper()
        clashes = User.objects.filter(username=value)
        if self.instance is not None:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError('An account with this ID already exists.')
        return value

    def profile_fields(self):
        """Profile-model field values to save. Extended by subclasses."""
        return {}

    def save(self):
        data = self.cleaned_data
        user = self.instance or User(role=self.role)
        user.username = data[self.id_field]
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.phone = data['phone']
        if data['password']:
            user.set_password(data['password'])
        user.save()
        self.profile_model.objects.update_or_create(user=user, defaults=self.profile_fields())
        return user


class StudentForm(AccountForm):
    id_field = 'matric_no'
    profile_model = StudentProfile
    role = User.Role.STUDENT

    matric_no = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    level = forms.ChoiceField(choices=StudentProfile.LEVELS, widget=forms.Select(attrs={'class': 'form-select'}))

    field_order = ['first_name', 'last_name', 'matric_no', 'level', 'email', 'phone', 'password']

    def initial_for(self, instance):
        return {
            **super().initial_for(instance),
            'matric_no': instance.student_profile.matric_no,
            'level': instance.student_profile.level,
        }

    def clean_matric_no(self):
        return self.clean_login_id(self.cleaned_data['matric_no'])

    def profile_fields(self):
        return {'matric_no': self.cleaned_data['matric_no'], 'level': self.cleaned_data['level']}


class LecturerForm(AccountForm):
    id_field = 'staff_id'
    profile_model = LecturerProfile
    role = User.Role.LECTURER

    staff_id = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))

    field_order = ['first_name', 'last_name', 'staff_id', 'email', 'phone', 'password']

    def initial_for(self, instance):
        return {**super().initial_for(instance), 'staff_id': instance.lecturer_profile.staff_id}

    def clean_staff_id(self):
        return self.clean_login_id(self.cleaned_data['staff_id'])

    def profile_fields(self):
        return {'staff_id': self.cleaned_data['staff_id']}
