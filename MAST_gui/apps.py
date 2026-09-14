import threading

from django.apps import AppConfig

from common.config import Config
from common.mast_logging import get_logger

from .context_processors import MastCache

logger = get_logger(__name__)


class MastGuiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "MAST_gui"

    def ready(self):
        """Called when Django starts"""
        # Avoid running twice in development (Django reloader spawns 2 processes)
        import os

        from .context_processors import MastCache

        if os.environ.get("RUN_MAIN") != "true":
            return

        # Opt-in by design (MAST_common#96): it starts a thread holding a change-stream
        # cursor, so it wants an owner with a lifetime, and Config() is also constructed
        # by manage.py one-shots and tests. Without this, get_sites()/get_thar_filters()/
        # local_site() all stay pinned to whatever was loaded at process start, forever --
        # the periodic MastCache refresh below only re-fetches live controller status, not
        # the configuration snapshot. Never fatal, and idempotent (safe under the dev
        # reloader's second process, though RUN_MAIN already filters that out above).
        Config().start_watching()

        logger.info("Django startup: initializing periodic cache refresh...")

        # Initial refresh in a separate thread to not block startup
        threading.Thread(target=self._initial_refresh, daemon=True).start()

        # Start periodic refresh thread
        def periodic_refresh():
            """Refresh cache every N seconds in a separate thread"""
            try:
                # Run refresh in a separate thread so it doesn't block
                refresh_thread = threading.Thread(target=self._refresh_and_broadcast, daemon=True)
                refresh_thread.start()

                # Schedule next refresh
                timer = threading.Timer(MastCache.TTL, periodic_refresh)
                timer.daemon = True
                timer.start()
            except Exception as e:
                logger.error(f"Periodic cache refresh error: {e}", exc_info=True)
                # Retry after TTL even on error
                timer = threading.Timer(MastCache.TTL, periodic_refresh)
                timer.daemon = True
                timer.start()

        # Start the periodic refresh cycle
        timer = threading.Timer(MastCache.TTL, periodic_refresh)  # First refresh in 30s
        timer.daemon = True
        timer.start()

        logger.info(f"Periodic cache refresh started (every {MastCache.TTL}s)")

    def _initial_refresh(self):
        """Initial cache refresh on startup"""
        # from .context_processors import refresh_cache
        # refresh_cache()
        MastCache().refresh()

    def _refresh_and_broadcast(self):
        """Refresh cache and broadcast activity indicator updates"""
        # from .context_processors import refresh_cache
        from .notification_handler import broadcast_activity_indicators_update

        # Refresh the cache
        # refresh_cache()
        MastCache().refresh()

        # Broadcast activity indicators to all connected browsers
        try:
            broadcast_activity_indicators_update()
        except Exception as e:
            logger.error(f"Error broadcasting activity indicators: {e}", exc_info=True)
