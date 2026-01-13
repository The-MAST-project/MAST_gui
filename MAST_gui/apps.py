from django.apps import AppConfig
import threading
import logging

logger = logging.getLogger(__name__)

class MastGuiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MAST_gui'
    
    def ready(self):
        """Called when Django starts"""
        from .context_processors import refresh_cache, _MAST_CACHE
        
        # Avoid running twice in development (Django reloader spawns 2 processes)
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        logger.info("Django startup: initializing periodic cache refresh...")
        
        # Initial refresh
        refresh_cache()
        
        # Start periodic refresh thread
        def periodic_refresh():
            """Refresh cache every N seconds"""
            try:
                ttl = _MAST_CACHE.get('ttl', 30)  # Default 30s
                refresh_cache()
                
                # Schedule next refresh
                timer = threading.Timer(ttl, periodic_refresh)
                timer.daemon = True  # Die when main thread dies
                timer.start()
            except Exception as e:
                logger.error(f"Periodic cache refresh error: {e}", exc_info=True)
                # Retry after TTL even on error
                timer = threading.Timer(30, periodic_refresh)
                timer.daemon = True
                timer.start()
        
        # Start the periodic refresh cycle
        timer = threading.Timer(30, periodic_refresh)  # First refresh in 30s
        timer.daemon = True
        timer.start()
        
        logger.info("Periodic cache refresh started (every 30s)")
