import logging
from pathlib import Path

import tomlkit

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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
@require_http_methods(['GET'])
def login_modal(request):
    return render(request, 'account/login_modal.html')


@require_http_methods(['GET'])
def social_force_select(request, provider):
    """Set a session flag so the next OAuth request forces account selection, then redirect."""
    request.session['social_force_select'] = True
    login_url = reverse(f'{provider}_login')
    return redirect(f'{login_url}?process=login')


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
def _send_approval_email(request, user):
    if user.email:
        send_mail(
            subject='Your MAST account has been approved',
            message=(
                f'Hi {user.get_full_name() or user.username},\n\n'
                f'Your account has been approved. You can now log in at:\n'
                f'{request.build_absolute_uri(reverse("login"))}\n\n'
                f'The MAST team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


def admin_approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_registered = True
    user.is_active = True
    user.save()
    everybody = Group.objects.get(name='Everybody')
    user.groups.add(everybody)
    _send_approval_email(request, user)
    messages.success(request, f'User {user.username} approved.')
    return render(request, 'admin/partials/user_row.html', {'user': user})


@login_required
@require_http_methods(['POST'])
def admin_reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    email = user.email
    user.delete()
    if email:
        send_mail(
            subject='Your MAST account request was not approved',
            message=(
                f'Hi {username},\n\n'
                f'Unfortunately your account request was not approved.\n\n'
                f'The MAST team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    return HttpResponse('')


def _transfer_plan_ownership(from_uid: str, to_uid: str):
    """Rewrite owner field in all plan TOML files from from_uid to to_uid."""
    plans_root = Path('/Storage/mast-share/MAST/plans')
    if not plans_root.exists():
        return
    for toml_file in plans_root.rglob('PLAN_*.toml'):
        try:
            text = toml_file.read_text(encoding='utf-8')
            doc = tomlkit.loads(text)
            if str(doc.get('owner', '')) == from_uid:
                doc['owner'] = to_uid
                toml_file.write_text(tomlkit.dumps(doc), encoding='utf-8')
        except Exception:
            logger.exception(f'Failed to transfer ownership in {toml_file}')


@login_required
@require_http_methods(['POST'])
def admin_deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.is_registered = False
    user.save()
    messages.success(request, f'User {user.username} deactivated.')
    return render(request, 'admin/partials/user_row.html', {'user': user})


@login_required
@require_http_methods(['GET'])
def admin_delete_user_modal(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin/partials/delete_user_modal.html', {'user': user})


@login_required
@require_http_methods(['POST'])
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    try:
        mast_user = User.objects.get(username='mast')
        _transfer_plan_ownership(str(user.uid), str(mast_user.uid))
    except User.DoesNotExist:
        pass
    user.delete()
    return HttpResponse('')


@login_required
@require_http_methods(['GET', 'POST'])
def profile_edit(request):
    """Self-service profile edit modal — no admin permission required."""
    return _user_edit(request, request.user, post_url=reverse('profile_edit'))


@login_required
@require_http_methods(['GET', 'POST'])
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return _user_edit(request, user, post_url=reverse('admin_user_edit', args=[user_id]))


@login_required
@require_http_methods(['GET', 'POST'])
@permission_required('accounts.can_manage_users', raise_exception=True)
def admin_approve_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return _user_edit(request, user, post_url=reverse('admin_approve_edit', args=[user_id]),
                      submit_label='Approve', approve=True)


def _user_edit(request, user, post_url, submit_label='Save', approve=False):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            if approve:
                user.is_active = True
                user.is_registered = True
                user.save(update_fields=['is_active', 'is_registered'])
                _send_approval_email(request, user)
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = ProfileForm(instance=user)
    social_providers = list(user.socialaccount_set.values_list('provider', flat=True))
    caps = sorted(set(
        perm.split('.', 1)[1]
        for perm in user.get_group_permissions()
        if perm.startswith('accounts.')
    ))
    return render(request, 'admin/partials/user_edit_modal.html', {
        'edit_user': user,
        'form': form,
        'social_providers': social_providers,
        'post_url': post_url,
        'submit_label': submit_label,
        'capabilities': caps,
    })
