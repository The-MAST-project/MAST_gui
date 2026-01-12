"""
Accounts views - User profile and authentication.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User, Group
from .forms import RegistrationForm, LocalSignupForm, ProfileForm
from views.urls import get_dynamic_url

logger = logging.getLogger('mast.accounts')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view"""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_registered:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name or user.username}!')
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(get_dynamic_url(request, next_url))
            else:
                messages.error(request, "Registration not approved yet or rejected.")
                return redirect(get_dynamic_url(request, 'accounts:login'))
        else:
            messages.error(request, "Invalid username or password.")
            return redirect(get_dynamic_url(request, 'accounts:login'))
    return render(request, get_dynamic_url(request, 'accounts/login.html'))

@require_http_methods(["GET", "POST"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect(get_dynamic_url(request, 'login'))


def profile_view(request):
    """User profile view"""
    if not request.user.is_authenticated:
        return redirect(get_dynamic_url(request, 'login'))
    
    return render(request, get_dynamic_url(request, 'accounts/profile.html'), {
        'user': request.user
    })


@login_required
def profile(request):
    """
    User profile view (for self-edit).
    """
    user = request.user
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(get_dynamic_url(request, 'profile'))
    else:
        form = ProfileForm(instance=user)
    return render(request, get_dynamic_url(request, 'registration/profile.html'), {'form': form})


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
    
    return render(get_dynamic_url(request, 'accounts/profile_modal.html'), context)


def user_switcher(request):
    """
    User switcher: login or register.
    """
    if not request.user.is_authenticated:
        # Default to guest if no session user
        guest = authenticate(request, username='guest')
        if guest:
            login(request, guest)
            messages.info(request, "Logged in as guest.")
            return redirect(get_dynamic_url(request, 'dashboard'))

    # ...existing code for login/register UI...
    return render(request, get_dynamic_url(request, 'accounts/user_switcher.html'))

def register(request):
    """
    Registration view: social or local.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_registered = False
            user.set_password(request.POST.get('password', ''))
            user.save()
            form.save_m2m()
            messages.info(request, "Registration submitted. Awaiting approval.")
            return redirect(get_dynamic_url(request, 'accounts:login'))
    else:
        form = RegistrationForm()
    return render(request, get_dynamic_url(request, 'accounts/register.html'), {'form': form})


def signup(request):
    """
    Social signup landing page (no form here).
    """
    return render(get_dynamic_url(request, 'registration/signup.html'))


def local_signup(request):
    """
    Local account registration view.
    """
    if request.method == "POST":
        form = LocalSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require admin approval
            user.save()
            return redirect(get_dynamic_url(request, 'login'))
    else:
        form = LocalSignupForm()
    return render(request, get_dynamic_url(request, 'registration/local_signup.html'), {'form': form})


@login_required
def admin_users(request):
    """
    User management page for admins.
    Shows all users, groups, and pending registrations.
    """
    User = get_user_model()
    users = User.objects.all().order_by('username')
    groups = Group.objects.all().order_by('name')
    # Pending registrations: users not yet approved
    pending_registrations = User.objects.filter(is_registered=False).order_by('-date_joined')
    return render(get_dynamic_url(request, 'admin/users.html'), {
        'users': users,
        'groups': groups,
        'pending_registrations': pending_registrations,
    })


@login_required
@require_http_methods(["POST"])
def admin_approve_user(request, user_id):
    """
    Approve a pending registration (HTMX action).
    """
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    user.is_registered = True
    user.save()
    messages.success(request, f"User {user.username} approved.")
    return render(get_dynamic_url(request, 'admin/partials/user_row.html'), {'user': user})


@login_required
@require_http_methods(["POST"])
def admin_reject_user(request, user_id):
    """
    Reject a pending registration (HTMX action).
    """
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f"User {user.username} rejected and deleted.")
    return HttpResponse('')


@login_required
@require_http_methods(["GET", "POST"])
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_user_edit(request, user_id):
    """
    Edit user details (HTMX modal or full page)
    """
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = ProfileForm(instance=user)
    return render(get_dynamic_url(request, 'admin/partials/user_edit_modal.html'), {
        'edit_user': user,
        'form': form,
    })
