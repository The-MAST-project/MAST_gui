import re
import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


def generate_username(first: str, middle: str = '', last: str = '') -> str:
    """Build a username from name parts: first.middle.last (lowercase, dots collapsed)."""
    parts = [first, middle, last]
    name = '.'.join(p.strip().lower() for p in parts if p.strip())
    name = re.sub(r'[^a-z0-9.]', '', name)   # strip non-alphanumeric except dots
    name = re.sub(r'\.{2,}', '.', name)       # collapse consecutive dots
    return name.strip('.') or 'user'


def unique_username(first: str, middle: str = '', last: str = '') -> str:
    """Generate a unique username, appending .2, .3 … if needed."""
    base = generate_username(first, middle, last)
    if not User.objects.filter(username=base).exists():
        return base
    i = 2
    while User.objects.filter(username=f'{base}.{i}').exists():
        i += 1
    return f'{base}.{i}'


def generate_display(first: str, last: str) -> str:
    """Build a display name: first.last (lowercase, dots collapsed)."""
    parts = [first.strip().lower(), last.strip().lower()]
    name = '.'.join(p for p in parts if p)
    name = re.sub(r'[^a-z0-9.]', '', name)
    name = re.sub(r'\.{2,}', '.', name)
    return name.strip('.') or 'user'


def unique_display(first: str, last: str, middle: str = '') -> str:
    """Generate a unique display name.

    Disambiguation order:
      1. first.last
      2. first.middle.last   (if middle is available and first.last is taken)
      3. first.last.2, first.last.3 … (numeric suffix as last resort)
    """
    base = generate_display(first, last)
    if not User.objects.filter(display=base).exists():
        return base
    if middle:
        initial = re.sub(r'[^a-z0-9]', '', middle.strip().lower())[:1]
        if initial:
            with_middle = re.sub(r'\.{2,}', '.', f'{base.split(".")[0]}.{initial}.{base.split(".")[-1]}')
            if not User.objects.filter(display=with_middle).exists():
                return with_middle
    i = 2
    while User.objects.filter(display=f'{base}.{i}').exists():
        i += 1
    return f'{base}.{i}'


class MASTPermissions:
    CAN_VIEW = 'can_view'
    CAN_SUBMIT_PLANS = 'can_submit_plans'
    CAN_MANAGE_PLANS = 'can_manage_plans'
    CAN_EXECUTE_PLANS = 'can_execute_plans'
    CAN_USE_CONTROLS = 'can_use_controls'
    CAN_CHANGE_CONFIGURATION = 'can_change_configuration'
    CAN_MANAGE_USERS = 'can_manage_users'

    ALL = [
        CAN_VIEW,
        CAN_SUBMIT_PLANS,
        CAN_MANAGE_PLANS,
        CAN_EXECUTE_PLANS,
        CAN_USE_CONTROLS,
        CAN_CHANGE_CONFIGURATION,
        CAN_MANAGE_USERS,
    ]


class User(AbstractUser):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    prefix = models.CharField(max_length=32, blank=True)
    middle = models.CharField(max_length=64, blank=True)
    affiliation = models.CharField(max_length=128, blank=True)
    display = models.CharField(max_length=64, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)

    @property
    def full_name(self) -> str:
        parts = [self.prefix, self.first_name, self.middle, self.last_name]
        return ' '.join(p for p in parts if p)

    def has_mast_permission(self, codename: str) -> bool:
        return self.has_perm(f'accounts.{codename}')

    class Meta:
        permissions = [
            ('can_view',                 'Can view MAST pages'),
            ('can_submit_plans',         'Can submit observation plans'),
            ('can_manage_plans',         'Can manage plans'),
            ('can_execute_plans',        'Can execute plans and batches'),
            ('can_use_controls',         'Can use low-level controls'),
            ('can_change_configuration', 'Can change configuration'),
            ('can_manage_users',         'Can manage users'),
        ]


@receiver(m2m_changed, sender=User.groups.through)
def sync_is_staff(sender, instance, action, pk_set, **kwargs):
    """Keep is_staff in sync with membership in the Admin group."""
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        admin_group = Group.objects.get(name='Admin')
        is_admin = instance.groups.filter(pk=admin_group.pk).exists()
        if instance.is_staff != is_admin:
            instance.is_staff = is_admin
            instance.save(update_fields=['is_staff'])
    except Group.DoesNotExist:
        pass
