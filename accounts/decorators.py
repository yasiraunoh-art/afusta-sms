from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    """Restrict a view to users whose `role` is in `roles`.

    Usage: @role_required('admin') or @role_required('admin', 'lecturer')
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You don't have access to that page.")
                return redirect('accounts:redirect_after_login')
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
