from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from allauth.socialaccount.providers.google.provider import GoogleProvider

        _original = GoogleProvider.get_auth_params_from_request

        def _patched(self, request, action):
            params = _original(self, request, action)
            if request.session.pop('social_force_select', False):
                params['prompt'] = 'select_account'
            return params

        GoogleProvider.get_auth_params_from_request = _patched
