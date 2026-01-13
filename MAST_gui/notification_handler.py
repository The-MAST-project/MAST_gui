import logging
import time
from .context_processors import _MAST_CACHE, _MAST_CACHE_LOCK
from common.models.statuses import ShortStatus

logger = logging.getLogger(__name__)

def update_cache_from_notification(notification):
    """
    Update _MAST_CACHE based on notification path
    Path format: [site, machine_type, machine_name?, component, ..., field]
    
    Cache structure (_MAST_CACHE['status'] is a SitesStatus object):
    - status.sites[site_name] → SiteStatus (dict access)
    - SiteStatus.units[unit_name] → UnitStatus (dict access)
    - SiteStatus.deepspec → DeepSpecStatus (attribute)
    - SiteStatus.highspec → HighSpecStatus (attribute)
    - SiteStatus.controller → ControllerStatus (attribute)
    - UnitStatus.focuser → FocuserStatus (attribute)
    - FocuserStatus.position → int (attribute)
    """
    if not notification.get('cache') or not notification['cache'].get('path'):
        return False
    
    try:
        path = notification['cache']['path']
        value = notification.get('value')
        
        if not path or value is None:
            return False
        
        # Parse path components
        site = path[0]
        machine_type = path[1]
        
        # Get SitesStatus object
        sites_status = _MAST_CACHE.get('status')
        if not sites_status:
            logger.warning("Cache status not initialized")
            return False
        
        # Navigate to SiteStatus - sites is a dict attribute
        if not hasattr(sites_status, 'sites') or site not in sites_status.sites:
            logger.warning(f"Site {site} not found in cache")
            return False
        
        site_status = sites_status.sites[site]
        
        # Handle different machine types
        if machine_type == 'unit':
            machine_name = path[2]
            dict_path = path[3:]  # ['focuser', 'position']
            
            # Get unit from units dict (units is an attribute, then dict access)
            if not hasattr(site_status, 'units') or not site_status.units:
                logger.warning(f"No units found for site {site}")
                return False
            
            if machine_name not in site_status.units:
                logger.warning(f"Unit {machine_name} not found in site {site}")
                return False
            
            if isinstance(site_status.units[machine_name], ShortStatus):
                logger.warning(f"Cannot update short status for unit {machine_name}")
                return False
            
            target = site_status.units[machine_name]
        
        elif machine_type == 'spec':
            spec_name = path[2]  # 'deepspec' or 'highspec'
            dict_path = path[3:]  # remaining path after spec name
            
            # Access spec as attribute
            if not hasattr(site_status, spec_name):
                logger.warning(f"Spec {spec_name} not found for site {site}")
                return False
            
            if getattr(site_status, spec_name).type == 'short':
                logger.warning(f"Cannot update short status for spec {spec_name}")
                return False
            
            target = getattr(site_status, spec_name)
        
        elif machine_type == 'controller':
            dict_path = path[2:]  # Everything after 'controller'
            
            # Access controller as attribute
            if not hasattr(site_status, 'controller'):
                logger.warning(f"Controller not found for site {site}")
                return False
            
            if getattr(site_status, 'controller').type == 'short':
                logger.warning(f"Cannot update short status for controller {site}")
                return False
            
            target = site_status.controller
        
        else:
            logger.warning(f"Unknown machine_type: {machine_type}")
            return False
        
        if target is None:
            logger.warning(f"Target is None for path: {path}")
            return False
        
        # Walk dict_path to leaf (all attributes in Pydantic models)
        for key in dict_path[:-1]:
            if not hasattr(target, key):
                logger.warning(f"Attribute {key} not found on {type(target).__name__}")
                return False
            target = getattr(target, key)
            if target is None:
                logger.warning(f"Path element {key} is None")
                return False
        
        # Set final value (always attribute in Pydantic models)
        final_key = dict_path[-1]
        if not hasattr(target, final_key):
            logger.warning(f"Final attribute {final_key} not found on {type(target).__name__}")
            return False
        
        with _MAST_CACHE_LOCK:
            setattr(target, final_key, value)        
            # Update cache timestamp
            _MAST_CACHE['last_refresh'] = time.time()
            
        logger.info(f"Cache updated: {'.'.join(map(str, path))} = {value}")
        return True
    
    except Exception as e:
        logger.error(f"Cache update error: {e}", exc_info=True)
        return False
