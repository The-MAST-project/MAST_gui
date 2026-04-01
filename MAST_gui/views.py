"""
Core views for site selection and basic pages
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
import queue
import uuid
import time
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
import logging
from pydantic import ValidationError
from views.urls import get_dynamic_url
import json
from .sse_manager import sse_manager

from accounts.models import User
from .notification_handler import update_sse_message_from_update_request
from .context_processors import MastCache, refresh_cache

# from .context_processors import refresh_cache, _MAST_CACHE

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def select_site(request):
    """
    Handle site selection from dropdown
    Stores selection in session and redirects to site dashboard
    """
    site_name = request.POST.get('site')
    if site_name:
        request.session['selected_site'] = site_name
    
    # Redirect to site dashboard page
    return redirect(get_dynamic_url(request, 'units:site_dashboard'))


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
def admin_groups(request):
    groups = Group.objects.all().order_by('name')
    return render(request, 'admin/groups.html', {'groups': groups})


def _mast_permissions():
    from django.contrib.auth.models import Permission
    from accounts.models import MASTPermissions
    codenames = [
        MASTPermissions.CAN_VIEW,
        MASTPermissions.CAN_SUBMIT_PLANS,
        MASTPermissions.CAN_MANAGE_PLANS,
        MASTPermissions.CAN_EXECUTE_PLANS,
        MASTPermissions.CAN_USE_CONTROLS,
        MASTPermissions.CAN_CHANGE_CONFIGURATION,
        MASTPermissions.CAN_MANAGE_USERS,
    ]
    return Permission.objects.filter(
        content_type__app_label='accounts',
        codename__in=codenames,
    ).order_by('codename')


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_group_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    mast_permissions = _mast_permissions()

    if request.method == 'POST':
        group.name = request.POST.get('name', group.name)
        selected_perms = request.POST.getlist('permissions')
        group.permissions.set(mast_permissions.filter(id__in=selected_perms))
        group.save()
        return HttpResponse(headers={'HX-Refresh': 'true'})

    return render(request, 'admin/partials/group_edit_modal.html', {
        'edit_group': group,
        'mast_permissions': mast_permissions,
        'members': group.user_set.order_by('username'),
    })


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_group_delete_modal(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    return render(request, 'admin/partials/group_delete_modal.html', {
        'group': group,
        'member_count': group.user_set.count(),
    })


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
@require_http_methods(["POST"])
def admin_group_delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group.delete()
    return HttpResponse(headers={'HX-Refresh': 'true'})


@csrf_exempt
@require_http_methods(["POST"])
def handle_notification(request):
    """
    Receive notifications from backend controller
    """
    from common.notifications import UiUpdateNotifications
    try:
        try:
            ui_notifications = UiUpdateNotifications.model_validate_json(request.body)
        except ValidationError as ve:
            logger.error(f"Notification validation error: {ve}")
            return JsonResponse({'error': 'Invalid notification format'}, status=400)
        
        initiator = ui_notifications.initiator
        logger.info(f"Received notification: {ui_notifications.type} from {initiator.site}:{initiator.hostname}")
        
        if sse_manager.client_count == 0:
            logger.info("No SSE clients connected, skipping broadcast")
            return JsonResponse({'broadcasted': False, 'reason': 'no_clients'})
        
        sse_message = update_sse_message_from_update_request(ui_notifications)
        data = sse_message.model_dump_json() if sse_message else None
        if data is not None:
            sse_manager.broadcast('notification', data)
            logger.info(f"Broadcast notification to {sse_manager.client_count} clients")
        
            return JsonResponse({'broadcasted': True})
        else:
            logger.warning("No data to broadcast from notification")
            return JsonResponse({'broadcasted': False, 'reason': 'no_data'})
    
    except Exception as e:
        logger.error(f"Notification handling error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def sse_stream(request):
    """
    Server-Sent Events endpoint for real-time notifications
    """
    client_id = str(uuid.uuid4())
    
    # Get client IP (check proxy headers first)
    client_ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
        request.META.get('HTTP_X_REAL_IP', '') or
        request.META.get('REMOTE_ADDR', 'unknown')
    )
    
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:50]
    
    logger.info(f"SSE client connecting: {client_id} from {client_ip} ({user_agent})")
    client_queue = sse_manager.add_client(client_id)
    
    def event_stream():
        """Generator that yields SSE formatted messages"""
        start_time = time.time()
        message_count = 0
        last_activity = time.time()  # Track last activity
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"
            
            while True:
                try:
                    # Wait for message with timeout (for keep-alive)
                    message = client_queue.get(timeout=15)  # Changed from 30 to 15 seconds
                    
                    # Format as SSE
                    event_type = message.get('event', 'message')
                    data = json.dumps(message.get('data', {}))
                    
                    # Send the event
                    yield f"event: {event_type}\n"
                    yield f"data: {data}\n\n"
                    message_count += 1
                    last_activity = time.time()
                    
                except queue.Empty:
                    # Send keep-alive comment
                    yield ": keep-alive\n\n"
                    
                    # Log if too long without messages
                    idle_time = time.time() - last_activity
                    if idle_time > 60:
                        logger.warning(f"SSE client {client_id} idle for {idle_time:.1f}s")
                
        except GeneratorExit:
            # Connection closed - log and cleanup (don't yield anything)
            duration = time.time() - start_time
            logger.info(f"SSE client {client_id} disconnected after {duration:.1f}s ({message_count} messages)")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"SSE client {client_id} error after {duration:.1f}s: {e}")
        finally:
            sse_manager.remove_client(client_id)
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response


_GRAFANA_DASHBOARD_URLS = {
    'linux':   '/grafana/d/rYdddlPWk/node-exporter-full',
    'windows': '/grafana/d/IV0hu1m7z/windows-exporter-dashboard',
}

@login_required
def grafana(request, tag=None):
    grafana_url = _GRAFANA_DASHBOARD_URLS.get(tag, '/grafana/dashboards/')
    return render(request, 'grafana.html', {'grafana_url': grafana_url})


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def manage_ownerships(request):
    users = User.objects.all().order_by('username')
    return render(request, 'admin/ownerships.html', {'users': users})


def _list_user_assets(user):
    """Return list of asset dicts for all plans owned by user."""
    from pathlib import Path
    import tomlkit

    plans_root = Path('/Storage/mast-share/MAST/plans')
    assets = []
    if not plans_root.exists():
        return assets
    for toml_file in plans_root.rglob('PLAN_*.toml'):
        try:
            doc = tomlkit.loads(toml_file.read_text(encoding='utf-8'))
            if str(doc.get('owner', '')) != str(user.uid):
                continue
            status = toml_file.parent.name
            target = doc.get('target', {})
            plan_name = target.get('name', '') if isinstance(target, dict) else ''
            ulid_val = doc.get('ulid', toml_file.stem.replace('PLAN_', ''))
            assets.append({
                'id': str(toml_file.relative_to(plans_root)),
                'name': f"{plan_name} ({ulid_val})" if plan_name else str(ulid_val),
                'type': 'Plan',
                'status': status,
            })
        except Exception:
            logger.exception(f'Failed to read plan {toml_file}')
    assets.sort(key=lambda a: a['status'])
    return assets


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
def ownerships_assets(request):
    from_user_id = request.GET.get('from_user_id')
    if not from_user_id:
        return HttpResponse('')
    from_user = get_object_or_404(User, id=from_user_id)
    assets = _list_user_assets(from_user)
    return render(request, 'admin/partials/ownership_assets.html', {
        'from_user': from_user,
        'assets': assets,
    })


@login_required
@permission_required('accounts.can_manage_users', raise_exception=True)
@require_http_methods(['POST'])
def ownerships_transfer(request):
    import json as _json
    import tomlkit
    from pathlib import Path

    try:
        body = _json.loads(request.body)
        from_user = get_object_or_404(User, id=body['from_user_id'])
        to_user = get_object_or_404(User, id=body['to_user_id'])
        asset_ids = body.get('asset_ids', [])

        if not asset_ids:
            return JsonResponse({'ok': False, 'error': 'No assets selected'})
        if from_user.id == to_user.id:
            return JsonResponse({'ok': False, 'error': 'From and To users must differ'})

        plans_root = Path('/Storage/mast-share/MAST/plans')
        errors = []
        transferred = 0
        for rel_path in asset_ids:
            toml_file = plans_root / rel_path
            try:
                doc = tomlkit.loads(toml_file.read_text(encoding='utf-8'))
                if str(doc.get('owner', '')) != str(from_user.uid):
                    errors.append(f'{rel_path}: owner mismatch')
                    continue
                doc['owner'] = str(to_user.uid)
                toml_file.write_text(tomlkit.dumps(doc), encoding='utf-8')
                transferred += 1
            except Exception as e:
                logger.exception(f'Failed to transfer {toml_file}')
                errors.append(f'{rel_path}: {e}')

        return JsonResponse({'ok': True, 'transferred': transferred, 'errors': errors})
    except Exception as e:
        logger.exception('ownerships_transfer error')
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def api_users(request):
    """Return [{uuid, display}] for all active users."""
    from django.http import JsonResponse
    from accounts.models import User
    users = (
        User.objects
        .filter(is_active=True)
        .exclude(display='')
        .values('uid', 'display')
    )
    return JsonResponse([{'uuid': str(u['uid']), 'display': u['display']} for u in users], safe=False)


@csrf_exempt
def debug_cache(request):
    """Debug endpoint to view cache contents"""
    # Auto-refresh if cache is empty
    if not MastCache().sites_status:
        logger.info("Cache empty, triggering refresh...")
        MastCache().refresh()
    
    # Use Pydantic's built-in JSON serialization (handles Enums automatically)
    status_data = None
    if MastCache().sites_status:
        status_data = MastCache().sites_status.model_dump(mode='json')
    
    cache_data = {
        'last_refresh': MastCache().last_refresh,
        'ttl': MastCache().ttl,
        'status': status_data
    }
    
    return JsonResponse(cache_data, safe=False, json_dumps_params={'indent': 2})


@csrf_exempt
@require_http_methods(["POST"])
def refresh_cache_endpoint(request):
    """Manually trigger cache refresh"""
    success = MastCache().refresh()
    data = {
        'success': success,
        'timestamp': MastCache().last_refresh,
        'has_status': MastCache().sites_status is not None
    }
    return JsonResponse(data, safe=False, json_dumps_params={'indent': 2})

