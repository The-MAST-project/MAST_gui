"""
Core views for site selection and basic pages
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import IntegrityError
import logging

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
    return redirect('units:list')


def dashboard(request):
    """
    Main dashboard/landing page
    """
    return render(request, 'dashboard.html')


@login_required
def admin_users(request):
    """
    User management page for admins
    Requires can_change_users permission
    """
    # Get all users and groups
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
    # For now, only mast-wis-control exists
    netdata_host = "mast-wis-control"
    netdata_url = f"http://{netdata_host}:19999"
    
    # For server-side proxy option, use a proxied URL
    proxy_url = f"/manage/netdata-proxy/?host={netdata_host}"
    
    return render(request, 'admin/resources.html', {
        'netdata_url': netdata_url,
        'proxy_url': proxy_url,
        'netdata_host': netdata_host,
    })


@login_required
@csrf_exempt  # Netdata makes requests without CSRF tokens
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
def admin_user_edit(request, user_id):
    """
    Edit user details (HTMX modal)
    """
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
@require_http_methods(["POST"])  # Change to only POST
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
