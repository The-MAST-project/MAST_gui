from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


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
    is_registered = models.BooleanField(default=False)
    prefix = models.CharField(max_length=16, blank=True)
    full_name = models.CharField(max_length=128, blank=True)
    affiliation = models.CharField(max_length=128, blank=True)

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
