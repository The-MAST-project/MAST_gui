"""
Context processors for MAST_gui.
Adds site information and user capabilities to all templates.
"""
import logging

logger = logging.getLogger('mast.dashboard')


def site_context(request):
    """
    Add site information to template context.
    """
    context = {
        'current_site': None,
        'all_sites': [],
        'user_capabilities': [],
    }
    
    try:
        from config import Config
        config = Config()
        
        # Get current site
        context['current_site'] = config.local_site
        
        # Get all sites
        context['all_sites'] = config.sites
        
        # Get user capabilities
        if request.user.is_authenticated:
            mongo_user = getattr(request.user, 'mongo_user', None)
            if not mongo_user:
                from accounts.backends import MongoDBAuthBackend
                backend = MongoDBAuthBackend()
                mongo_user = backend.get_mongo_user(request.user)
                request.user.mongo_user = mongo_user
            
            if mongo_user:
                context['user_capabilities'] = mongo_user.capabilities
    
    except Exception as e:
        logger.error(f"Error loading site context: {e}")
    
    return context
