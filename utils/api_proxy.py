"""
Proxy decorator for GUI views that call backend endpoints.
Validates endpoint is GUI-accessible and user has required capability.
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from common.decorators import is_gui_endpoint, get_endpoint_capability
from common.api import ControlApi
from .permissions import user_has_capability
import inspect

def proxy_backend(view_func):
    """
    Decorator for Django views that proxy backend API calls.
    Automatically validates endpoint access and user capabilities.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # The view should return (api_instance, method_name, *args)
        # Or just make the call and we validate after
        result = view_func(request, *args, **kwargs)
        
        # If view returns a tuple, extract backend call info
        if isinstance(result, tuple) and len(result) >= 2:
            api_instance, method_name = result[:2]
            method_args = result[2:] if len(result) > 2 else ()
            
            # Get the actual backend method
            backend_method = getattr(api_instance, method_name, None)
            if backend_method is None:
                return JsonResponse({
                    'error': f'Backend method {method_name} not found'
                }, status=500)
            
            # Check if method is GUI-exposed
            if not is_gui_endpoint(backend_method):
                return JsonResponse({
                    'error': f'Endpoint {method_name} not exposed to GUI'
                }, status=403)
            
            # Check user capability
            required_cap = get_endpoint_capability(backend_method)
            if required_cap and not user_has_capability(request.user, required_cap):
                return JsonResponse({
                    'error': f'Missing required capability: {required_cap}'
                }, status=403)
            
            # Make the actual backend call
            response = backend_method(*method_args)
            
            # Handle CanonicalResponse
            if hasattr(response, 'succeeded'):
                if response.succeeded:
                    return JsonResponse({'success': True, 'data': response.value})
                else:
                    return JsonResponse({
                        'success': False,
                        'errors': response.errors
                    }, status=400)
            
            return JsonResponse(response)
        
        # If view already made the call and returned response
        return result
    
    return wrapper
