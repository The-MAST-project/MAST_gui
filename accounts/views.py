"""
Accounts views - User profile and authentication.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('mast.accounts')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view"""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name or user.username}!')
            
            # Redirect to next page or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def profile_view(request):
    """User profile view"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def profile(request):
    """User profile page."""
    user = request.user
    
    # Get user's groups and permissions
    groups = user.groups.all()
    permissions = user.user_permissions.all()
    
    # Get all permissions through groups
    group_permissions = set()
    for group in groups:
        group_permissions.update(group.permissions.all())
    
    # Combine direct and group permissions
    all_permissions = set(permissions) | group_permissions
    
    # Define all possible MAST capabilities
    from accounts.models import MASTPermissions
    capabilities = [
        {'code': MASTPermissions.CAN_VIEW, 'name': 'View system status and data'},
        {'code': MASTPermissions.CAN_CHANGE_CONFIGURATION, 'name': 'Change system configuration'},
        {'code': MASTPermissions.CAN_USE_CONTROLS, 'name': 'Use system controls'},
        {'code': MASTPermissions.CAN_CHANGE_USERS, 'name': 'Manage users and groups'},
        {'code': MASTPermissions.CAN_OWN_TASKS, 'name': 'Create and own observation tasks'},
    ]
    
    # Check which capabilities the user has
    for cap in capabilities:
        cap['has_permission'] = user.has_perm(f'auth.{cap["code"]}')
    
    # Determine authentication origin
    # TODO: Add social auth detection when implemented
    auth_origin = 'Local Account'
    
    context = {
        'page_title': 'Profile',
        'user': user,
        'groups': groups,
        'capabilities': capabilities,
        'auth_origin': auth_origin,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_modal(request):
    """User profile modal content (for HTMX)"""
    user = request.user
    
    # Get user's groups and permissions
    groups = user.groups.all()
    
    # Define all possible MAST capabilities
    from accounts.models import MASTPermissions
    capabilities = [
        {'code': MASTPermissions.CAN_VIEW, 'name': 'View system status and data'},
        {'code': MASTPermissions.CAN_CHANGE_CONFIGURATION, 'name': 'Change system configuration'},
        {'code': MASTPermissions.CAN_USE_CONTROLS, 'name': 'Use system controls'},
        {'code': MASTPermissions.CAN_CHANGE_USERS, 'name': 'Manage users and groups'},
        {'code': MASTPermissions.CAN_OWN_TASKS, 'name': 'Create and own observation tasks'},
    ]
    
    # Check which capabilities the user has
    for cap in capabilities:
        cap['has_permission'] = user.has_perm(f'auth.{cap["code"]}')
    
    # Determine authentication origin
    auth_origin = 'Local Account'
    
    context = {
        'user': user,
        'groups': groups,
        'capabilities': capabilities,
        'auth_origin': auth_origin,
    }
    
    return render(request, 'accounts/profile_modal.html', context)
