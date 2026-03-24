import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.forms import RegistrationForm, LocalSignupForm, ProfileForm
from accounts.models import User, MASTPermissions

logger = logging.getLogger('mast.accounts')


_CAPABILITIES = [
    (MASTPermissions.CAN_VIEW,                 'View system status and data'),
    (MASTPermissions.CAN_SUBMIT_PLANS,         'Submit observation plans'),
    (MASTPermissions.CAN_MANAGE_PLANS,         'Manage plans'),
    (MASTPermissions.CAN_EXECUTE_PLANS,        'Execute plans and batches'),
    (MASTPermissions.CAN_USE_CONTROLS,         'Use low-level controls'),
    (MASTPermissions.CAN_CHANGE_CONFIGURATION, 'Change configuration'),
    (MASTPermissions.CAN_MANAGE_USERS,         'Manage users'),
]


def _build_capabilities(user):
    return [
        {'code': code, 'name': name, 'has_permission': user.has_perm(f'accounts.{code}')}
        for code, name in _CAPABILITIES
    ]


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name or user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def profile_modal(request):
    user = request.user
    return render(request, 'accounts/profile_modal.html', {
        'user': user,
        'groups': user.groups.all(),
        'capabilities': _build_capabilities(user),
    })


@login_required
def user_profile(request, uid):
    """Readonly profile page for any user, linked from plan owner names."""
    target = get_object_or_404(User, uid=uid)
    return render(request, 'accounts/user_profile.html', {
        'profile_user': target,
        'groups': target.groups.all(),
        'capabilities': _build_capabilities(target),
        'is_own_profile': target == request.user,
        'can_manage_users': request.user.has_perm('accounts.can_manage_users'),
    })


def signup(request):
    return render(request, 'registration/signup.html')


def local_signup(request):
    if request.method == 'POST':
        form = LocalSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.is_registered = False
            user.save()
            messages.info(request, 'Registration submitted. Awaiting admin approval.')
            return redirect('login')
    else:
        form = LocalSignupForm()
    return render(request, 'registration/local_signup.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_registered = False
            user.set_password(request.POST.get('password', ''))
            user.save()
            form.save_m2m()
            messages.info(request, 'Registration submitted. Awaiting admin approval.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ── Admin user management (kept for legacy URL compatibility; prefer Django /admin/) ──

@login_required
def admin_users(request):
    return render(request, 'admin/users.html', {
        'users': User.objects.all().order_by('username'),
        'groups': Group.objects.all().order_by('name'),
        'pending_registrations': User.objects.filter(is_registered=False).order_by('-date_joined'),
    })


@login_required
@require_http_methods(['POST'])
def admin_approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_registered = True
    user.is_active = True
    user.save()
    messages.success(request, f'User {user.username} approved.')
    return render(request, 'admin/partials/user_row.html', {'user': user})


@login_required
@require_http_methods(['POST'])
def admin_reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return HttpResponse('')


@login_required
@require_http_methods(['GET', 'POST'])
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'admin/partials/user_edit_modal.html', {'edit_user': user, 'form': form})
