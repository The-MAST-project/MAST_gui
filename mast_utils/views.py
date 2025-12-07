"""
Utility views for HTMX endpoints and common functionality.
"""
import logging
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from common.api import ControllerApi
import asyncio
from common.config import Config

logger = logging.getLogger('mast.mast_utils')


@login_required
@require_http_methods(["GET"])
def controller_status_check(request):
    """
    HTMX endpoint for polling controller status.
    Returns updated status indicator HTML.
    """
    site = request.session.get('selected_site', 'wis')
    
    # Get full site configuration
    config = Config()
    sites = config.get_sites()
    site_obj = next((s for s in sites if s.name == site), None)
    
    if not site_obj:
        # Fallback if site not found
        controller_host = f'mast-{site}-control'
        site_name = site.upper()
    else:
        # Use controller_host from site configuration
        controller_host = site_obj.controller_host
        site_name = site_obj.name
    
    # Create ControllerApi with site_name parameter
    controller = ControllerApi(site_name=site)
    
    try:
        response = asyncio.run(controller.client.get("status", timeout=3))
        connected = response.succeeded
        error = None if response.succeeded else str(response.errors)
        
        # Reset retry count on success
        if connected:
            request.session['controller_retry_count'] = 0
            retry_count = 0
        else:
            retry_count = request.session.get('controller_retry_count', 0)
            request.session['controller_retry_count'] = retry_count + 1
            retry_count += 1
            
    except Exception as e:
        logger.debug(f"Controller check failed: {e}")
        connected = False
        error = str(e)
        retry_count = request.session.get('controller_retry_count', 0) + 1
        request.session['controller_retry_count'] = retry_count
    
    # Determine if we should show banner (>30s = >2 failed checks at 15s interval)
    show_banner = not connected and retry_count >= 2
    
    return render(request, 'components/controller_status.html', {
        'connected': connected,
        'error': error,
        'retry_count': retry_count,
        'last_check': datetime.now(),
        'controller_host': controller_host,
        'site_name': site_name,
        'show_banner': show_banner,
    })
