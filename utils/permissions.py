"""
Permission decorators using Django's built-in permission system.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, permission_required
from accounts.models import MASTPermissions, get_permission_full_name


def mast_permission_required(*permission_codes):
    """
    Decorator that checks if user has required MAST permissions.
    
    Usage:
        @mast_permission_required(MASTPermissions.CAN_VIEW)
        def my_view(request):
            ...
        
        @mast_permission_required(MASTPermissions.CAN_USE_CONTROLS, MASTPermissions.CAN_CHANGE_CONFIGURATION)
        def admin_view(request):
            ...
    """
    # Convert to full permission names
    full_perms = [get_permission_full_name(code) for code in permission_codes]
    
    def decorator(view_func):
        # Use Django's built-in permission_required decorator
        @wraps(view_func)
        @login_required
        @permission_required(full_perms, raise_exception=True)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common permissions
view_required = lambda func: mast_permission_required(MASTPermissions.CAN_VIEW)(func)
control_required = lambda func: mast_permission_required(MASTPermissions.CAN_USE_CONTROLS)(func)
config_required = lambda func: mast_permission_required(MASTPermissions.CAN_CHANGE_CONFIGURATION)(func)
admin_required = lambda func: mast_permission_required(MASTPermissions.CAN_CHANGE_USERS)(func)
