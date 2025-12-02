"""
Custom authentication backend that integrates Django with MongoDB user configuration.
"""
import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

try:
    from common.config import Config
    from config.identification import UserConfig
except ImportError:
    # MAST_common not available yet
    Config = None
    UserConfig = None

logger = logging.getLogger('mast.accounts')


class MongoDBAuthBackend(BaseBackend):
    """
    Authenticates against MongoDB configuration database.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user against MongoDB.
        Username is expected to be an email address.
        """
        if not Config or not username or not password:
            return None
        
        # Normalize email to lowercase
        email = username.lower()
        
        try:
            config = Config()
            mongo_user = config.get_user(email)
            
            if not mongo_user:
                logger.debug(f"User {email} not found in MongoDB")
                return None
            
            # Check if user has local password (not social auth only)
            if not mongo_user.password:
                logger.debug(f"User {email} has no local password (social auth only)")
                return None
            
            # Verify password
            if not check_password(password, mongo_user.password):
                logger.debug(f"Invalid password for user {email}")
                return None
            
            # Get or create Django User for session management
            user = self._get_or_create_django_user(mongo_user)
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID for session restoration.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def _get_or_create_django_user(self, mongo_user):
        """
        Get or create a Django User object from MongoDB UserConfig.
        Django User is used only for session management.
        Actual permissions come from MongoDB.
        """
        try:
            user = User.objects.get(email=mongo_user.name)
        except User.DoesNotExist:
            # Create Django user
            user = User.objects.create_user(
                username=mongo_user.name,  # email as username
                email=mongo_user.name,
                first_name=mongo_user.full_name.split()[0] if mongo_user.full_name else '',
                last_name=' '.join(mongo_user.full_name.split()[1:]) if mongo_user.full_name else '',
            )
            user.set_unusable_password()  # Password handled by MongoDB
            user.save()
            logger.info(f"Created Django user for {mongo_user.name}")
        
        return user
    
    def get_mongo_user(self, django_user):
        """
        Get MongoDB UserConfig for a Django User.
        """
        if not Config:
            return None
            
        try:
            config = Config()
            return config.get_user(django_user.email)
        except Exception as e:
            logger.error(f"Error fetching MongoDB user for {django_user.email}: {e}")
            return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has a specific MAST capability.
        """
        if not user_obj.is_active:
            return False
        
        mongo_user = self.get_mongo_user(user_obj)
        if not mongo_user:
            return False
        
        # Map Django permissions to MAST capabilities
        capability_map = {
            'view': 'canView',
            'change_configuration': 'canChangeConfiguration',
            'use_controls': 'canUseControls',
            'change_users': 'canChangeUsers',
            'own_tasks': 'canOwnTasks',
        }
        
        capability = capability_map.get(perm)
        if capability:
            return capability in mongo_user.capabilities
        
        return False
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if user has any permissions in the given app.
        """
        if not user_obj.is_active:
            return False
        
        mongo_user = self.get_mongo_user(user_obj)
        if not mongo_user:
            return False
        
        return 'canView' in mongo_user.capabilities
