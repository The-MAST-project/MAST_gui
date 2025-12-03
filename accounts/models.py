"""
Custom permissions for MAST system.
All authorization handled by Django's built-in Groups & Permissions.
"""
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class MASTPermissions:
    """
    MAST permission codes that map to your capabilities.
    These are created as Django permissions.
    """
    CAN_VIEW = 'can_view'
    CAN_CHANGE_CONFIGURATION = 'can_change_configuration'
    CAN_USE_CONTROLS = 'can_use_controls'
    CAN_CHANGE_USERS = 'can_change_users'
    CAN_OWN_TASKS = 'can_own_tasks'
    
    @classmethod
    def get_all_permissions(cls):
        """Get all permission codes"""
        return [
            (cls.CAN_VIEW, 'Can view system status and data'),
            (cls.CAN_CHANGE_CONFIGURATION, 'Can change system configuration'),
            (cls.CAN_USE_CONTROLS, 'Can use system controls'),
            (cls.CAN_CHANGE_USERS, 'Can manage users and groups'),
            (cls.CAN_OWN_TASKS, 'Can create and own observation tasks'),
        ]


def get_permission_full_name(codename: str) -> str:
    """Convert permission codename to Django's full permission name"""
    return f'auth.{codename}'


# Add helper methods to User model
def user_has_mast_permission(self, permission_code: str) -> bool:
    """Check if user has a MAST permission"""
    return self.has_perm(get_permission_full_name(permission_code))

User.add_to_class('has_mast_permission', user_has_mast_permission)
