"""
Core views for site selection and basic pages
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
import logging
import json
from views.urls import get_dynamic_url

from accounts.models import User
from .notification_handler import update_cache_from_notification
from .context_processors import refresh_cache, _MAST_CACHE  # Add _MAST_CACHE here

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def select_site(request):
    """
    Handle site selection from dropdown
    Stores selection in session and redirects to units page
    """
    site_name = request.POST.get('site')
    if site_name:
        request.session['selected_site'] = site_name
    
    # Redirect to units page for the new site
    return redirect(get_dynamic_url(request, 'units:list'))


def dashboard(request):
    """
    Main dashboard/landing page
    """
    return render(request, 'dashboard.html')


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_users(request):
    """
    User management page for admins
    Requires can_manage_users permission
    """
    # Use the custom User model directly, do NOT call get_user_model() here
    users = User.objects.all().order_by('username')
    groups = Group.objects.all().order_by('name')
    
    # TODO: Implement actual signup request system
    # For now, show pending users (inactive users) as "signup requests"
    signup_requests = User.objects.filter(is_active=False).order_by('-date_joined')
    return render(request, 'admin/users.html', {
        'users': users,
        'groups': groups,
        'signup_requests': signup_requests,
    })


@login_required
def admin_resources(request):
    """
    System resources monitoring page (Netdata iframe)
    """
    # Use the new Netdata URL
    netdata_url = (
        "http://localhost:19999/spaces/theblumz-space/rooms/mast-wis-control-local/nodes"
        "#metrics_correlation=false&after=-900&before=0&utc=Asia%2FJerusalem"
        "&offset=%2B2&timezoneName=Jerusalem&modal=&modalTab=&_o=zc7BCoJAGATgd9lzP6it69oLRBBdii4R8rs7pqAuuKsR0btH0qFbhy7dZmAYvrswNQ9hxx1o4lasRId-LPY3H9BRJBYC0KrUcU5VJi3JJAVprZhSqdnkMkYm5alHsBy44Av6ULTOcHsm-nbdO4uNPbi1-xxsmwmFH8u5ZKmOqiwtCXmiSFbRkrSxMS0Tm8dJBGWN-gn5Mvhjg-uc_kfjMUwYPAVn9uDB1G-UeDwB"
    )
    proxy_url = netdata_url  # No proxy, direct link

    return render(request, 'admin/resources.html', {
        'netdata_url': netdata_url,
        'proxy_url': proxy_url,
        'netdata_host': "mast-wis-control",
    })


@csrf_exempt
@login_required
def netdata_proxy(request, netdata_path=''):
    """
    Proxy Netdata requests through Django to bypass client proxy.
    This fetches from Netdata server-side and returns to client.
    Handles both root path and sub-paths like /api/v1/registry
    """
    host = request.GET.get('host', 'mast-wis-control')
    
    # Build the full URL with path and query string
    netdata_url = f"http://{host}:19999/{netdata_path}"
    
    # Preserve query string (but remove 'host' param as it's not for Netdata)
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        # Remove 'host' parameter from query string
        from urllib.parse import parse_qs, urlencode
        params = parse_qs(query_string)
        params.pop('host', None)
        if params:
            netdata_url += f'?{urlencode(params, doseq=True)}'
    
    try:
        # Forward the request with the same method (GET/POST/etc)
        method = request.method.lower()
        req_func = getattr(requests, method)
        
        # Forward headers (excluding host-specific ones)
        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in ['host', 'cookie', 'authorization']
        }
        
        # Make the request
        response = req_func(
            netdata_url,
            headers=headers,
            data=request.body if request.method == 'POST' else None,
            timeout=10,
            allow_redirects=False  # Don't follow redirects automatically
        )
        
        # Return the response
        django_response = HttpResponse(
            response.content,
            content_type=response.headers.get('content-type', 'text/html'),
            status=response.status_code
        )
        
        # Forward important headers
        for header in ['location', 'set-cookie']:
            if header in response.headers:
                django_response[header] = response.headers[header]
        
        return django_response
        
    except requests.RequestException as e:
        return HttpResponse(f"Error connecting to Netdata: {e}", status=502)


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_user_edit(request, user_id):
    """
    Edit user details (HTMX modal)
    """
    # Use the correct User model import (do not reassign User)
    user = get_object_or_404(User, id=user_id)
    groups = Group.objects.all().order_by('name')
    
    if request.method == 'POST':
        # Update user details
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        
        # Update groups
        selected_groups = request.POST.getlist('groups')
        user.groups.clear()
        for group_id in selected_groups:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully')
        
        # Return updated user row for HTMX to swap
        return render(request, 'admin/partials/user_row.html', {
            'user': user
        })
    
    # Show edit form
    return render(request, 'admin/partials/user_edit_modal.html', {
        'edit_user': user,
        'groups': groups,
    })


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
@require_http_methods(["POST"])
def admin_user_delete(request, user_id):
    """
    Delete user (with confirmation)
    """
    user = get_object_or_404(User, id=user_id)
    
    # Don't allow deleting yourself
    if user.id == request.user.id:
        messages.error(request, "You cannot delete your own account")
        return render(request, 'admin/partials/user_row.html', {'user': user}, status=400)
    
    # Don't allow deleting superusers (extra safety)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser accounts")
        return render(request, 'admin/partials/user_row.html', {'user': user}, status=400)
    
    username = user.username
    user_id_to_delete = user.id
    
    # Use Django's collector to see what will be deleted
    from django.contrib.admin.utils import NestedObjects
    from django.db import DEFAULT_DB_ALIAS
    
    collector = NestedObjects(using=DEFAULT_DB_ALIAS)
    collector.collect([user])
    
    logger.info(f'About to delete user {username} (id={user_id_to_delete})')
    logger.info(f'Related objects to be deleted: {collector.nested()}')
    
    try:
        # Delete with CASCADE - this should delete all related objects automatically
        count, deleted = user.delete()
        logger.info(f'User {username} deleted successfully. Deleted {count} objects: {deleted}')
        messages.success(request, f'User {username} deleted successfully')
        
        # Verify deletion
        if User.objects.filter(id=user_id_to_delete).exists():
            logger.error(f'ERROR: User {username} still exists after delete()!')
            return HttpResponse('ERROR: User still exists', status=500)
        
        return HttpResponse('', content_type='text/html')
        
    except IntegrityError as e:
        logger.error(f'IntegrityError deleting user {username}: {e}')
        # Reload user from DB (it might have been partially deleted)
        try:
            user = User.objects.get(id=user_id_to_delete)
            user.is_active = False
            user.save()
            messages.warning(request, f'Cannot delete user {username} (has protected related data). User has been deactivated.')
            return render(request, 'admin/partials/user_row.html', {'user': user})
        except User.DoesNotExist:
            # User was actually deleted despite the error
            logger.info(f'User {username} was deleted despite IntegrityError')
            return HttpResponse('', content_type='text/html')


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_group_edit(request, group_id):
    """
    Edit group details and permissions
    """
    from django.contrib.auth.models import Permission
    
    group = get_object_or_404(Group, id=group_id)
    all_permissions = Permission.objects.filter(
        content_type__app_label='auth'
    ).order_by('name')
    
    if request.method == 'POST':
        group.name = request.POST.get('name', group.name)
        
        # Update permissions
        selected_perms = request.POST.getlist('permissions')
        group.permissions.clear()
        for perm_id in selected_perms:
            perm = Permission.objects.get(id=perm_id)
            group.permissions.add(perm)
        
        group.save()
        messages.success(request, f'Group {group.name} updated successfully')
        
        return render(request, 'admin/partials/group_row.html', {
            'group': group
        })
    
    return render(request, 'admin/partials/group_edit_modal.html', {
        'edit_group': group,
        'all_permissions': all_permissions,
    })


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
@require_http_methods(["POST"])
def admin_group_delete(request, group_id):
    """
    Delete group
    """
    group = get_object_or_404(Group, id=group_id)
    group_name = group.name
    group.delete()
    messages.success(request, f'Group {group_name} deleted successfully')
    
    # Return empty response
    return HttpResponse('')


@csrf_exempt
@require_http_methods(["POST"])
def handle_notification(request):
    """
    Receive notifications from backend controller
    """
    try:
        notification = json.loads(request.body)
        
        logger.info(f"Received notification: {notification.get('type')}")
        
        success = False
        # Update cache
        if notification.get('cache'):
            success = update_cache_from_notification(notification)
        
        # TODO: Implement SSE broadcast
        # TODO: Implement toast card generation
        
        return JsonResponse({'success': success})
    
    except Exception as e:
        logger.error(f"Notification handling error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def debug_cache(request):
    """Debug endpoint to view cache contents"""
    # Auto-refresh if cache is empty
    if not _MAST_CACHE.get('status'):
        logger.info("Cache empty, triggering refresh...")
        refresh_cache()
    
    # Use Pydantic's built-in JSON serialization (handles Enums automatically)
    status_data = None
    if _MAST_CACHE.get('status'):
        status_data = _MAST_CACHE['status'].model_dump(mode='json')
    
    cache_data = {
        'last_refresh': _MAST_CACHE.get('last_refresh'),
        'ttl': _MAST_CACHE.get('ttl'),
        'status': status_data
    }
    
    return JsonResponse(cache_data, safe=False, json_dumps_params={'indent': 2})


@csrf_exempt
@require_http_methods(["POST"])
def refresh_cache_endpoint(request):
    """Manually trigger cache refresh"""
    success = refresh_cache()
    
    return JsonResponse({
        'success': success,
        'timestamp': _MAST_CACHE.get('last_refresh'),
        'has_status': _MAST_CACHE.get('status') is not None
    })


# Django's built-in Group model fields:
# - id: AutoField (primary key)
# - name: CharField (unique, required)
# - permissions: ManyToManyField to Permission
#
# Example:
#   from django.contrib.auth.models import Group
#   group = Group.objects.create(name="everybody")
#   group.permissions.add(permission_obj)
#   group.name  # group name
#   group.permissions.all()  # queryset of Permission objects

# Django Permission model:
# - Represents a specific action a user/group can perform (e.g., "add_user", "change_group")
# - Fields:
#   - id: AutoField (primary key)
#   - name: Human-readable name (e.g., "Can add user")
#   - codename: Short string (e.g., "add_user")
#   - content_type: ForeignKey to ContentType (the model this permission applies to)
#
#   perm = Permission.objects.get(codename="add_user")
#   user.user_permissions.add(perm)
#   group.permissions.add(perm)
#
# Django auto-creates add/change/delete/view permissions for each model.
# Custom permissions can be defined in a model's Meta class.
# Django auto-creates add/change/delete/view permissions for each model.
# Custom permissions can be defined in a model's Meta class.
