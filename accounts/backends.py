import logging
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

logger = logging.getLogger('mast.accounts')


class LocalUserBackend(BaseBackend):
    """
    Custom backend kept for future local override use.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class RegisteredUserBackend(ModelBackend):
    """
    Extends Django's ModelBackend with an is_active gate.
    Users must be explicitly approved before they can log in.
    Admin group members are granted all permissions (replaces is_superuser).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_active:
                return user
        except User.DoesNotExist:
            return None
        return None

    def _is_admin(self, user_obj):
        return user_obj.is_active and \
               user_obj.groups.filter(name='Admin').exists()

    def has_perm(self, user_obj, perm, obj=None):
        if self._is_admin(user_obj):
            return True
        return super().has_perm(user_obj, perm, obj)

    def has_module_perms(self, user_obj, app_label):
        if self._is_admin(user_obj):
            return True
        return super().has_module_perms(user_obj, app_label)
