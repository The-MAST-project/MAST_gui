from django.apps import AppConfig
import threading
import logging

logger = logging.getLogger(__name__)

class MastGuiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MAST_gui'
    
    def ready(self):
        """Called when Django starts"""
        from .context_processors import refresh_cache, _MAST_CACHE_TTL
        
        # Avoid running twice in development (Django reloader spawns 2 processes)
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        logger.info("Django startup: initializing periodic cache refresh...")
        
        # Initial refresh in a separate thread to not block startup
        threading.Thread(target=refresh_cache, daemon=True).start()
        
        # Start periodic refresh thread
        def periodic_refresh():
            """Refresh cache every N seconds in a separate thread"""
            try:
                ttl = _MAST_CACHE_TTL  # Use TTL from context_processors
                
                # Run refresh in a separate thread so it doesn't block
                refresh_thread = threading.Thread(target=refresh_cache, daemon=True)
                refresh_thread.start()
                
                # Schedule next refresh
                timer = threading.Timer(ttl, periodic_refresh)
                timer.daemon = True
                timer.start()
            except Exception as e:
                logger.error(f"Periodic cache refresh error: {e}", exc_info=True)
                # Retry after TTL even on error
                timer = threading.Timer(_MAST_CACHE_TTL, periodic_refresh)
                timer.daemon = True
                timer.start()
        
        # Start the periodic refresh cycle
        timer = threading.Timer(_MAST_CACHE_TTL, periodic_refresh)  # First refresh in 120s
        timer.daemon = True
        timer.start()
        
        logger.info(f"Periodic cache refresh started (every {_MAST_CACHE_TTL}s)")