"""
Dashboard views - Main landing page and site overview.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger('mast.dashboard')


@login_required
def index(request):
    """Main dashboard view."""
    try:
        from common.config import Config
        config = Config()
        
        # Get current site
        site = config.local_site
        
        context = {
            'site': site,
            'page_title': 'Dashboard',
        }
        
        return render(request, 'dashboard/index.html', context)
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render(request, 'dashboard/index.html', {
            'error': 'Error loading dashboard data'
        })
