"""
Custom authentication backend that validates against MongoDB
but uses Django's User model for session management.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from common.config import Config


class MongoSyncBackend(ModelBackend):
    """
    Authentication backend that:
    1. Checks credentials against MongoDB
    2. Creates/updates Django User on successful login
    3. Uses Django sessions for subsequent requests
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate against MongoDB, sync to Django User"""
        if username is None or password is None:
            return None
        
        # Check credentials in MongoDB
        try:
            config = Config()
            mongo_user = config.get_user(username)
            
            if not mongo_user:
                return None
            
            # TODO: Implement proper password hashing
            if mongo_user.password != password:
                return None
            
            # Create or update Django user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': mongo_user.email or '',
                    'first_name': mongo_user.full_name or '',
                    'is_active': True,
                }
            )
            
            if not created:
                # Update existing user
                user.email = mongo_user.email or ''
                user.first_name = mongo_user.full_name or ''
                user.save()
            
            return user
            
        except Exception:
            return None
    
    def get_user(self, user_id):
        """Get user from Django database"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
