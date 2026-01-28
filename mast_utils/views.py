"""
Utility views for HTMX endpoints and common functionality.
"""
import logging
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('mast.mast_utils')
@login_required
@require_http_methods(["GET"])
def django_controller_status_check(request):
    """
    HTMX endpoint for polling controller status.
    Returns updated status indicator HTML.
    """
    site = request.session.get('selected_site', 'wis')
    # Use mast context processor to get status dict
    from MAST_gui.context_processors import mast as mast_cache
    for s in mast_cache(request=request).sites_config:
        if s.name == site:
            controller_host = s.controller_host
            break

    error = None
    retry_count = 1
    show_banner = True
    return render(request, 'components/controller_status.html', {
        'connected': True,
        'error': error,
        'retry_count': retry_count,
        'last_check': datetime.now(),
        'controller_host': controller_host,
        'show_banner': show_banner,
    })
