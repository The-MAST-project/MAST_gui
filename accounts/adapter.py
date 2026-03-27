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
    def pre_social_login(self, request, sociallogin):
        """Auto-connect social account to existing account with matching email."""
        import logging
        log = logging.getLogger(__name__)
        log.warning("pre_social_login: is_existing=%s emails=%s",
                    sociallogin.is_existing,
                    [e.email for e in sociallogin.email_addresses])
        if sociallogin.is_existing:
            return
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for email_address in sociallogin.email_addresses:
            email = email_address.email
            # Check allauth EmailAddress table first
            try:
                existing = EmailAddress.objects.get(email__iexact=email)
                log.warning("pre_social_login: connecting via EmailAddress to user %s", existing.user)
                sociallogin.user = existing.user
                return
            except EmailAddress.DoesNotExist:
                pass
            # Fall back to User.email
            try:
                user = User.objects.get(email__iexact=email)
                log.warning("pre_social_login: connecting via User.email to user %s", user)
                sociallogin.user = user
                return
            except User.DoesNotExist:
                pass
        log.warning("pre_social_login: no existing user found")

    def save_user(self, request, sociallogin, form=None):
        from accounts.models import unique_username
        user = super().save_user(request, sociallogin, form)
        user.username = unique_username(user.first_name, '', user.last_name)
        user.is_active = False
        user.is_registered = False
        user.save()
        return user
