"""
Context processors to make data available to all templates
"""
import logging
import sys
from pathlib import Path

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
