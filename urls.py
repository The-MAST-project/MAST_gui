"""
Core views for site selection and basic pages
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
import logging
from views.urls import get_dynamic_url

logger = logging.getLogger(__name__)


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
    User = get_user_model()
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


# Django's built-in Group model fields:
# - id: AutoField (primary key)
# - name: CharField (unique, required)
# - permissions: ManyToManyField to Permission

# Example:
# from django.contrib.auth.models import Group
# group = Group.objects.create(name="everybody")
# group.permissions.add(permission_obj)
# group.name  # group name
# group.permissions.all()  # queryset of Permission objects

# Django Permission model:
# - Represents a specific action a user/group can perform (e.g., "add_user", "change_group").
# - Fields:
#   - id: AutoField (primary key)
#   - name: Human-readable name (e.g., "Can add user")
#   - codename: Short string (e.g., "add_user")
#   - content_type: ForeignKey to ContentType (the model this permission applies to)
#
# Permissions are assigned to users or groups.
# Example:
#   from django.contrib.auth.models import Permission
#   perm = Permission.objects.get(codename="add_user")
#   user.user_permissions.add(perm)
#   group.permissions.add(perm)
#
# Django auto-creates add/change/delete/view permissions for each model.
# Custom permissions can be defined in a model's Meta class.