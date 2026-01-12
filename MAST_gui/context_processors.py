"""
Context processors to make data available to all templates
"""
import logging
import sys
from pathlib import Path

import time
from common.config import Config
from common.api import ControllerApi
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Add common submodule to Python path
common_path = Path(__file__).parent.parent / 'common'
if str(common_path) not in sys.path:
    sys.path.insert(0, str(common_path))

try:
    from config import Config
    HAS_CONFIG = True
except ImportError as e:
    logger.error(f"Error importing Config: {e}")
    Config = None
    HAS_CONFIG = False


def site_data(request):
    """
    Make site information available in all templates
    """
    # Default values
    sites = []
    current_site = 'wis'
    current_site_obj = None
    
    if HAS_CONFIG:
        try:
            # Get all sites from config
            sites = Config().get_sites()
            
            # Get currently selected site from session (default to 'wis')
            current_site = request.session.get('selected_site', 'wis')
            
            # Find the current site object by name
            current_site_obj = next((s for s in sites if s.name == current_site), None)
            
            # If not found, use first local site as fallback
            if not current_site_obj and sites:
                current_site_obj = next((s for s in sites if s.local), sites[0] if sites else None)
                
        except Exception as e:
            logger.error(f"Error loading site context: {e}", exc_info=True)
    
    return {
        'all_sites': sites,
        'current_site': current_site,
        'current_site_obj': current_site_obj,
    }


"""
Context processors for adding global template variables.
"""

logger = logging.getLogger('mast.context_processors')


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
    
    # Try to connect to controller with site_name parameter
    controller = ControllerApi(site_name=site)
    
    try:
        response = asyncio.run(controller.client.get("status", timeout=3))
        status = {
            'connected': response.succeeded,
            'last_check': datetime.now(),
            'error': None if response.succeeded else str(response.errors),
            'retry_count': 0,
            'controller_host': controller_host,
        }
        
        # Reset retry count on success
        if response.succeeded:
            request.session['controller_retry_count'] = 0
        
    except Exception as e:
        logger.warning(f"Cannot connect to controller {controller_host}: {e}")
        
        # Increment retry count
        retry_count = request.session.get('controller_retry_count', 0)
        request.session['controller_retry_count'] = retry_count + 1
        
        status = {
            'connected': False,
            'last_check': datetime.now(),
            'error': str(e),
            'retry_count': retry_count + 1,
            'controller_host': controller_host,
        }
    
    return {'controller_status': status}

logger = logging.getLogger('mast.context_processors')

# In-memory cache for config and status (simple, per-process)
_MAST_CACHE = {
    'sites': [],
    'status': {},
    'last_refresh': 0,
    'ttl': 30,  # seconds
}

def mast(request):
    """
    Provides 'mast' context:
      mast.sites: list of all configured sites
      mast.status: dict {site_name: status}
    """
    now = time.time()
    cache = _MAST_CACHE
    needs_refresh = (now - cache['last_refresh'] > cache['ttl']) or not cache['sites']

    if needs_refresh:
        try:
            config = Config()
            sites = config.get_sites()
            cache['sites'] = sites
            # Query status for all sites via ControllerApi('status')
            # Use the first controller found (assume all sites managed by it)
            if sites:
                controller = ControllerApi()
                resp = controller.client.get("status")
                # If resp is a coroutine, run it
                if hasattr(resp, '__await__'):
                    import asyncio
                    resp = asyncio.run(resp)
                if resp and getattr(resp, 'succeeded', False) and isinstance(resp.value, dict):
                    cache['status'] = resp.value
                else:
                    cache['status'] = {}
            else:
                cache['status'] = {}
            cache['last_refresh'] = now
        except Exception as e:
            logger.warning(f"Error refreshing mast context: {e}")
            cache['status'] = {}
            cache['sites'] = []
            cache['last_refresh'] = now

    return {
        'mast': {
            'sites': cache['sites'],
            'status': cache['status'],
        }
    }
