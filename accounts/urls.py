from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=StyledAuthenticationForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('after-login/', views.redirect_after_login, name='redirect_after_login'),
    path('register/', views.register_student, name='register_student'),
    path('settings/', views.account_settings, name='settings'),
    path('lecturers/new/', views.create_lecturer, name='create_lecturer'),
]
