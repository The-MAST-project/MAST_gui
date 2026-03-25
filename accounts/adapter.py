from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.is_registered = False  # Require approval
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        from accounts.models import unique_username
        user = super().save_user(request, sociallogin, form)
        user.username = unique_username(user.first_name, '', user.last_name)
        user.is_active = False
        user.is_registered = False
        user.save()
        return user
