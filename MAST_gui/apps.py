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
        
        # Initial refresh in a separate thread to not block startup
        threading.Thread(target=self._initial_refresh, daemon=True).start()
        
        # Start periodic refresh thread
        def periodic_refresh():
            """Refresh cache every N seconds in a separate thread"""
            try:
                ttl = _MAST_CACHE.get('ttl', 30)  # Default 30s
                
                # Run refresh in a separate thread so it doesn't block
                refresh_thread = threading.Thread(target=self._refresh_and_broadcast, daemon=True)
                refresh_thread.start()
                
                # Schedule next refresh
                timer = threading.Timer(ttl, periodic_refresh)
                timer.daemon = True
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
    
    def _initial_refresh(self):
        """Initial cache refresh on startup"""
        from .context_processors import refresh_cache
        refresh_cache()
    
    def _refresh_and_broadcast(self):
        """Refresh cache and broadcast activity indicator updates"""
        from .context_processors import refresh_cache
        from .notification_handler import broadcast_activity_indicators_update
        
        # Refresh the cache
        refresh_cache()
        
        # Broadcast activity indicators to all connected browsers
        try:
            broadcast_activity_indicators_update()
        except Exception as e:
            logger.error(f"Error broadcasting activity indicators: {e}", exc_info=True)