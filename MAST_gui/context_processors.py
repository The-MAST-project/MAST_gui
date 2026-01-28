"""
Context processors to make data available to all templates
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from threading import Lock
from typing import ClassVar
from pydantic import BaseModel, Field

import time
from common.config import Config
from common.api import ControllerApi
from datetime import datetime
import asyncio
from common.models.statuses import SitesStatus
from common.config.site import Site

logger = logging.getLogger(__name__)

# Add common submodule to Python path
common_path = Path(__file__).parent.parent / 'common'
if str(common_path) not in sys.path:
    sys.path.insert(0, str(common_path))

# try:
#     from config import Config
#     HAS_CONFIG = True
# except ImportError as e:
#     logger.error(f"Error importing Config: {e}")
#     Config = None
#     HAS_CONFIG = False


def site_data(request):
    """
    Make site information available in all templates
    """
    # Default values
    sites = []
    current_site = 'wis'
    current_site_obj = None
    

    # Get all sites from config
    sites = Config().get_sites()
    
    # Get currently selected site from session (default to 'wis')
    current_site = request.session.get('selected_site', 'wis')
    
    # Find the current site object by name
    current_site_obj = next((s for s in sites if s.name == current_site), None)
    
    # If not found, use first local site as fallback
    if not current_site_obj and sites:
        current_site_obj = next((s for s in sites if s.local), sites[0] if sites else None)
    
    return {
        'all_sites': sites,
        'current_site': current_site,
        'current_site_obj': current_site_obj,
    }


"""
Context processors for adding global template variables.
"""

logger = logging.getLogger('mast.context_processors')


# _MAST_CACHE_LOCK: Lock = Lock()
# _MAST_CACHE_TTL = 120  # Default TTL for periodic refresh

# # In-memory cache for config and status (simple, per-process)
# _MAST_CACHE = {
#     'sites_config': [],
#     'sites_status': {},
#     'last_refresh': 0,
#     'controller_last_check': None,  # Add this
#     'controller_connected': False,  # Add this
#     'controller_error': None,  # Add this
#     'ttl': _MAST_CACHE_TTL,  # seconds,
# }

def controller_status(request):
    """
    Add controller connection status to all templates.
    
    Returns dict with:
        - connected: bool
        - last_check: datetime
        - error: str or None
        - retry_count: int
    """
    # Get site from session
    site = request.session.get('selected_site', 'wis')
    
    # Get controller_host from site configuration
    from common.config import Config
    config = Config()
    sites = config.get_sites()
    site_obj = next((s for s in sites if s.name == site), None)
    
    if not site_obj:
        # Fallback if site not found
        controller_host = f'mast-{site}-control'
    else:
        # Use controller_host from site configuration
        controller_host = site_obj.controller_host
    
    # Return cached status instead of checking every time
    return {
        'controller_status': {
            'connected': MastCache().controller_connected,
            'last_check': MastCache().controller_last_check,
            'error': MastCache().controller_error,
            'retry_count': request.session.get('controller_retry_count', 0),
            'controller_host': controller_host,
        }
    }

def refresh_cache():
    """
    Force refresh the cache from backend.
    Call this on Django startup or when cache is empty.
    """
    return MastCache().refresh()

# def refresh_cache():
#     """
#     Force refresh the cache from backend.
#     Call this on Django startup or when cache is empty.
#     """
#     # logger.info("Force refreshing cache from backend...")
    
#     try:
#         config = Config()
#         sites = config.get_sites()
#         _MAST_CACHE['sites_config'] = sites
        
#         # Query status from controller
#         if sites:
#             controller = ControllerApi()
            
#             # Get status endpoint - returns SitesStatus
#             resp = controller.get("status")
            
#             # Handle async response
#             if hasattr(resp, '__await__'):
#                 resp = asyncio.run(resp)
            
#             # Update controller connection status in cache
#             check_time = datetime.now()
            
#             # Check if response succeeded and parse as SitesStatus
#             if resp and getattr(resp, 'succeeded', False) and resp.value:
#                 # resp.value should be dict that can be parsed as SitesStatus

#                 with _MAST_CACHE_LOCK:
#                     _MAST_CACHE['sites_status'] = SitesStatus(**resp.value) if isinstance(resp.value, dict) else resp.value
                    
#                     # Update controller connection status
#                     _MAST_CACHE['controller_connected'] = True
#                     _MAST_CACHE['controller_last_check'] = check_time
#                     _MAST_CACHE['controller_error'] = None
                
#                 for site in _MAST_CACHE['sites_status'].sites.keys():
#                     msg = f"Status cache: [{site}]: "
#                     site_status = _MAST_CACHE['sites_status'].sites[site]
#                     controller_status = site_status.controller
#                     deepspec_status = site_status.spec.deepspec
#                     highspec_status = site_status.spec.highspec
#                     unit_statuses = site_status.units
#                     for comp_name, st in {'controller': controller_status, 'deepspec': deepspec_status, 'highspec': highspec_status}.items():
#                         msg += f"{comp_name}({type(st).__name__}), "
#                     for unit_name, unit_status in unit_statuses.items():
#                         msg += f"{unit_name}({type(unit_status).__name__}), "
#                     logger.info(msg)
#             else:
#                 error_msg = getattr(resp, 'errors', 'Unknown error')
#                 logger.warning(f"Failed to fetch status from backend: {error_msg}")
#                 with _MAST_CACHE_LOCK:
#                     _MAST_CACHE['sites_status'] = None
#                     _MAST_CACHE['controller_connected'] = False
#                     _MAST_CACHE['controller_last_check'] = check_time
#                     _MAST_CACHE['controller_error'] = str(error_msg)
#         else:
#             logger.warning("No sites configured")
#             with _MAST_CACHE_LOCK:
#                 _MAST_CACHE['sites_status'] = None
#                 _MAST_CACHE['controller_connected'] = False
#                 _MAST_CACHE['controller_last_check'] = datetime.now()
#                 _MAST_CACHE['controller_error'] = "No sites configured"
            
#         _MAST_CACHE['last_refresh'] = time.time()
#         return True
        
#     except Exception as e:
#         logger.error(f"Error refreshing cache: {e}", exc_info=True)
#         with _MAST_CACHE_LOCK:
#             _MAST_CACHE['sites_status'] = None
#             _MAST_CACHE['sites_config'] = []
#             _MAST_CACHE['controller_connected'] = False
#             _MAST_CACHE['controller_last_check'] = datetime.now()
#             _MAST_CACHE['controller_error'] = str(e)
#             _MAST_CACHE['last_refresh'] = time.time()
#         return False

class MastCache(BaseModel):
    _instance: ClassVar['MastCache' | None] = None
    _initialized: ClassVar[bool] = False

    TTL: ClassVar[int] = 120  # Default TTL for cache in seconds
    
    # Define Pydantic fields with proper type annotations
    sites_config: list[Site] | None = None
    sites_status: SitesStatus | None = None
    controller_connected: bool = False
    controller_last_check: datetime | None = None
    controller_error: str | None = None
    last_refresh: float | None = None
    
    # Non-serializable fields excluded from Pydantic validation
    lock: Lock = Field(default_factory=Lock, exclude=True, repr=False)
    ttl: int = Field(default=TTL, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True  # Allows Lock and other complex types
    
    def __new__(cls, **kwargs):
        if cls._instance is None:
            cls._instance = super(MastCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        if not MastCache._initialized:
            super().__init__(**kwargs)
            MastCache._initialized = True

    def refresh(self):
        """
        Force refresh the cache from backend.
        Call this on Django startup or when cache is empty.
        """
    # logger.info("Force refreshing cache from backend...")
    
        try:
            config = Config()
            sites = config.get_sites()
            self.sites_config = sites
            
            # Query status from controller
            if sites:
                controller = ControllerApi()
                
                # Get status endpoint - returns SitesStatus
                resp = controller.get("status")
            
                # Handle async response
                if hasattr(resp, '__await__'):
                    resp = asyncio.run(resp)
                
                # Update controller connection status in cache
                check_time = datetime.now()
                
                # Check if response succeeded and parse as SitesStatus
                if resp and getattr(resp, 'succeeded', False) and resp.value:
                    # resp.value should be dict that can be parsed as SitesStatus

                    with self.lock:
                        self.sites_status = SitesStatus(**resp.value) if isinstance(resp.value, dict) else resp.value
                        
                        # Update controller connection status
                        self.controller_connected = True
                        self.controller_last_check = check_time
                        self.controller_error = None
                    
                    for site in self.sites_status.sites.keys():
                        msg = f"Status cache: [{site}]: "
                        site_status = self.sites_status.sites[site]
                        controller_status = site_status.controller
                        deepspec_status = site_status.spec.deepspec
                        highspec_status = site_status.spec.highspec
                        unit_statuses = site_status.units
                        for comp_name, st in {'controller': controller_status, 'deepspec': deepspec_status, 'highspec': highspec_status}.items():
                            msg += f"{comp_name}({type(st).__name__}), "
                        for unit_name, unit_status in unit_statuses.items():
                            msg += f"{unit_name}({type(unit_status).__name__}), "
                        logger.info(msg)
                else:
                    error_msg = getattr(resp, 'errors', 'Unknown error')
                    logger.warning(f"Failed to fetch status from backend: {error_msg}")
                    with self.lock:
                        self.sites_status = None
                        self.controller_connected = False
                        self.controller_last_check = check_time
                        self.controller_error = str(error_msg)
            else:
                logger.warning("No sites configured")
                with self.lock:
                    self.sites_status = None
                    self.controller_connected = False
                    self.controller_last_check = datetime.now()
                    self.controller_error = "No sites configured"
                
            self.last_refresh = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}", exc_info=True)
            with self.lock:
                self.sites_status = None
                self.sites_config = []
                self.controller_connected = False
                self.controller_last_check = datetime.now()
                self.controller_error = str(e)
                self.last_refresh = time.time()
            return False

# def mast(request) -> MastCache:
def mast(request) -> MastCache:
    """Called automatically when rendering templates"""
    # now = time.time()
    # cache = _MAST_CACHE
    # needs_refresh = (now - cache['last_refresh'] > cache['ttl']) or not cache.get('sites_status')

    # if needs_refresh:
    #     refresh_cache()  # ← Called every 30s or if cache empty

    # return MastCache(
    #     sites_config=cache['sites_config'],
    #     sites_status=cache.get('sites_status', None),
    # )
    now = time.time()
    cache = MastCache()
    needs_refresh = (cache.last_refresh is None or now - cache.last_refresh > cache.ttl) or not cache.sites_status

    if needs_refresh:
        cache.refresh()  # ← Called every 30s or if cache empty
    return cache

    # return {
    #     'mast': {
    #         'sites': cache['sites_config'],
    #         'status': cache['sites_status'],
    #     }
    # }
