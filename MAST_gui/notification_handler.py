import logging
import time
from pydantic import BaseModel
from .context_processors import MastCache
from common.models.statuses import BasicStatus
from common.notifications import UiUpdateNotifications, NotificationInitiator, NotificationCardType

logger = logging.getLogger(__name__)

def update_cache_from_update_request(update_notifications: UiUpdateNotifications):
    """
    Update in-memory cache from notification update request
    """
        
    # Get SitesStatus object
    # sites_status = _MAST_CACHE.get('status')
    sites_status = MastCache().sites_status
    if not sites_status or not hasattr(sites_status, 'sites'):
        logger.warning("Cache status not initialized")
        return False
    
    # Do we have a cache entry for the update_notifications.initiator.site?
    if update_notifications.initiator.site not in sites_status.sites:
        logger.warning(f"Site {update_notifications.initiator.site} not found in cache")
        return False
    site_key = update_notifications.initiator.site
    if site_key not in sites_status.sites:
        logger.warning(f"Site {site_key} not found in cache")
        return False
    
    site_status = sites_status.sites[site_key]
    match update_notifications.initiator.type:
        case 'unit':
            type_key = 'units'
        case 'controller' | 'deepspec' | 'highspec':
            type_key = update_notifications.initiator.type
        case _:
            logger.warning(f"Unknown initiator type: {update_notifications.initiator.type}")
            return False
    if type_key not in site_status:
        logger.warning(f"Type {type_key} not found in site status")
        return False
    
    host_key = update_notifications.initiator.hostname
    if host_key not in site_status[type_key]:
        logger.warning(f"Host {host_key} not found in type {type_key}")
        return False
    
    target = site_status[type_key][host_key] if type_key == 'units' else site_status[type_key]
    if isinstance(target, BasicStatus):
        logger.warning(f"Target for {type_key} {host_key} is BasicStatus, cannot update attributes")
        return False
    
    for update_message in update_notifications.notifications:
        logger.debug(f"Update message: {update_message}")

        if not update_message.cache:
            logger.warning("No cache info in update message")
            continue
    
        try:
            dict_path = update_message.cache.path
            value = update_message.cache.value
        
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
            
            with MastCache._lock:
                setattr(target, final_key, value)        
                # Update cache timestamp
                MastCache().last_refresh = time.time()
                
            logger.info(f"Cache updated: {'.'.join(map(str, dict_path))} = {value}")
            return True
        
        except Exception as e:
            logger.error(f"Cache update error: {e}", exc_info=True)
            return False

class CardSSEMessage(BaseModel):
    """
    Allows initiator to request a card notification be displayed in the UI
    """
    type: NotificationCardType = 'info'  # 'info'|'error'|'warning'|'start'|'end'
    message: str | None = None
    details: list[str] = []
    duration: str | None = None  # For 'end' type cards
    component: str | None = None
    data: dict | None = None  # Machine-readable payload (e.g. motion target)

def card_sses_from_update_request(update_request: UiUpdateNotifications) -> list[CardSSEMessage] | None:
    """
    Generate toast card data from notification
    
    Returns list of CardSSEMessage dicts
    """
    card_sse_messages = []  # Change: create a list

    for notification in update_request.notifications:
        if not notification.card:
            continue  # No card in this message

        try:
            card_sse_message = CardSSEMessage(
                type=notification.card.type,
                message=notification.card.message,
                details=notification.card.details,
                duration=notification.card.duration,
                component=notification.card.component,
                data=notification.card.data,
            )
                
            card_sse_messages.append(card_sse_message.model_dump())  # Change: append to list
        
        except Exception as e:
            logger.error(f"Error generating toast card: {e}", exc_info=True)
            continue  # Change: continue to next message instead of return
    
    return card_sse_messages if card_sse_messages else None  # Change: return list or None

class DomSSEMessage(BaseModel):
    id: str
    text: str | None = None
    html: str | None = None

def dom_sses_from_update_request(update_request: UiUpdateNotifications) -> list[DomSSEMessage] | None:
    """
    Generate DOM update messages from notification
    """
    dom_sse_messages = []
    
    for notification in update_request.notifications:
        if not notification.dom:
            continue  # No DOM update in this message
        
        dom_update_message = notification.dom
        
        try:
            id=dom_update_message.id
            match dom_update_message.render_as:
                case 'text':
                    dom_sse_message = DomSSEMessage(
                        id=id,
                        text=str(notification.cache.value) if notification.cache else '',
                    )
                case 'badge':
                    html = ''
                    if isinstance(notification.cache.value, list):
                        values = notification.cache.value
                        for value in values:
                            html += f'<span class="badge bg-primary me-1">{str(value)}</span>'

                    dom_sse_message = DomSSEMessage(
                        id=id,
                        html=html if len(html) > 0 else '<span class="badge bg-secondary me-1">Idle</span>',
                    )
                case _:
                    logger.warning(f"Unknown DOM render_as: '{dom_update_message.render_as}'")
                    continue
                
            dom_sse_messages.append(dom_sse_message.model_dump())
        
        except Exception as e:
            logger.error(f"Error generating DOM update message: {e}", exc_info=True)
            return None
    
    return dom_sse_messages if dom_sse_messages else None

class UpdateSSEMessage(BaseModel):
    initiator: NotificationInitiator | None = None
    cards: list[CardSSEMessage] | None = None
    doms: list[DomSSEMessage] | None = None

def update_sse_message_from_update_request(update_request: UiUpdateNotifications) -> UpdateSSEMessage | None:
    """
    Generate SSE message from notification update request
    """
    try:
        update_sse_message = UpdateSSEMessage(
            initiator=update_request.initiator,
            cards=card_sses_from_update_request(update_request),
            doms=dom_sses_from_update_request(update_request)
        )
        if len(update_sse_message.cards or []) == 0 and len(update_sse_message.doms or []) == 0:
            return None
        
        return update_sse_message
    
    except Exception as e:
        logger.error(f"Error generating SSE message from update request: {e}", exc_info=True)
        return None

def broadcast_activity_indicators_update():
    """
    Broadcast activity indicator updates for all sites after cache refresh.
    Called after periodic cache refresh in apps.py.
    """
    # from .context_processors import _MAST_CACHE
    from .sse_manager import sse_manager
    
    # sites_status = _MAST_CACHE.get('status')
    sites_status = MastCache().sites_status
    if not sites_status or not hasattr(sites_status, 'sites'):
        logger.warning("No status in cache, skipping activity indicators broadcast")
        return
    
    for site_name, site_status in sites_status.sites.items():
        # Build update message with all component activities for this site
        activities_update = {
            'type': 'activity_indicators_refresh',
            'site': site_name,
            'components': {}
        }
        
        # Add controller activities
        if hasattr(site_status, 'controller') and site_status.controller:
            activities_update['components']['controller'] = getattr(
                site_status.controller, 'activities_verbal', []
            )
        
        # Add spec activities
        if hasattr(site_status, 'spec') and site_status.spec:
            activities_update['components']['spec'] = getattr(
                site_status.spec, 'activities_verbal', []
            )
        
        # Add unit activities
        if hasattr(site_status, 'units') and site_status.units:
            for unit_name, unit_status in site_status.units.items():
                activities_update['components'][unit_name] = getattr(
                    unit_status, 'activities_verbal', []
                )
        
        # Broadcast to all connected clients
        sse_manager.broadcast('activity_refresh', activities_update)
        logger.debug(f"Broadcast activity refresh for site {site_name}: {len(activities_update['components'])} components")
