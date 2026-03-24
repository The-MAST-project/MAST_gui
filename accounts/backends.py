import logging
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

logger = logging.getLogger('mast.accounts')


class LocalUserBackend(BaseBackend):
    """
    Custom backend for local users 'guest' and 'admin'.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username == 'guest':
            try:
                user, _ = User.objects.get_or_create(username='guest', defaults={'is_active': True})
                user.set_unusable_password()
                user.save()
                return user
            except Exception:
                return None
        if username == 'admin':
            try:
                user, _ = User.objects.get_or_create(username='admin', defaults={'is_active': True, 'is_staff': True, 'is_superuser': True})
                if password == 'physics':
                    return user
            except Exception:
                return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class RegisteredUserBackend(ModelBackend):
    """
    Extends Django's ModelBackend with an is_registered gate.
    Users must be explicitly approved before they can log in.
    Admin group members are granted all permissions (replaces is_superuser).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_registered:
                return user
        except User.DoesNotExist:
            return None
        return None

    def _is_admin(self, user_obj):
        return user_obj.is_active and user_obj.is_registered and \
               user_obj.groups.filter(name='Admin').exists()

    def has_perm(self, user_obj, perm, obj=None):
        if self._is_admin(user_obj):
            return True
        return super().has_perm(user_obj, perm, obj)

    def has_module_perms(self, user_obj, app_label):
        if self._is_admin(user_obj):
            return True
        return super().has_module_perms(user_obj, app_label)
