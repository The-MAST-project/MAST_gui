"""
Permission decorators and utilities for MAST.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def capability_required(capability):
    """
    Decorator to check if user has a specific MAST capability.
    
    Usage:
        @capability_required('canChangeConfiguration')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Get MongoDB user
            mongo_user = getattr(request.user, 'mongo_user', None)
            if not mongo_user:
                from accounts.backends import MongoDBAuthBackend
                backend = MongoDBAuthBackend()
                mongo_user = backend.get_mongo_user(request.user)
                request.user.mongo_user = mongo_user
            
            if mongo_user and capability in mongo_user.capabilities:
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("You don't have permission to access this resource.")
        
        return wrapped_view
    return decorator


def has_capability(user, capability):
    """
    Check if user has a specific capability.
    
    Usage:
        if has_capability(request.user, 'canUseControls'):
            ...
    """
    mongo_user = getattr(user, 'mongo_user', None)
    if not mongo_user:
        from accounts.backends import MongoDBAuthBackend
        backend = MongoDBAuthBackend()
        mongo_user = backend.get_mongo_user(user)
        user.mongo_user = mongo_user
    
    return mongo_user and capability in mongo_user.capabilities
