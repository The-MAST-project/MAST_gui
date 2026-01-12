"""
Permission decorators and utilities for MAST.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def capability_required(capability):
    """
    Decorator to check if user has a specific Django permission (capability).
    
    Usage:
        @capability_required('canChangeConfiguration')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(f'accounts.{capability}'):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You don't have permission to access this resource.")
        
        return wrapped_view
    return decorator


def has_capability(user, capability):
    """
    Check if user has a specific Django permission (capability).
    
    Usage:
        if has_capability(request.user, 'canUseControls'):
            ...
    """
    return user.has_perm(f'accounts.{capability}')
