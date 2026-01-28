"""
Dashboard views - Main landing page and site overview.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from common.config import Config
from common.api import ControllerApi
from common.models.statuses import UnitStatus, ShortUnitStatus, FullUnitStatus
import asyncio

logger = logging.getLogger('mast.dashboard')


@login_required
def index(request):
    """Main dashboard view."""
    try:
        # Get current site from session
        current_site = request.session.get('selected_site', 'wis')
        # Get mast context from context processor
        mast = request.context.get('mast') if hasattr(request, 'context') else None
        if not mast:
            from MAST_gui.context_processors import mast as mast_cache
            mast = mast_cache(request)
        mast_sites = mast.sites_config
        site = next((s for s in mast_sites if s.name == current_site), None)
        if not site:
            return render(request, 'dashboard/index.html', {
                'error': f'Site {current_site} not found'
            })
        # Get status dict for all sites
        mast_statuses = mast.sites_status
        site_status = mast_statuses.get(current_site, {})
        
        units_status = []
        
        for building in site.buildings:
            for unit_id in building.units:
                status_info = {
                    'name': unit_id,
                    'building': building.names[0] if building.names else "Unknown",
                    'status': 'unknown',
                    'deployed': unit_id in site.deployed_units
                }
                
                unit_status = next((us for us in site_status.get('units', []) if us['name'] == unit_id), None)
                logger.info(unit_status)
                if unit_status:
                    status_info['status'] = 'operational' if unit_status['operational'] else 'error'
                    status_info['powered'] = unit_status['powered']
                    status_info['detected'] = unit_status['detected']
                    status_info['guiding'] = unit_status.get('guiding', False)
                    status_info['autofocusing'] = unit_status.get('autofocusing', False)
                    status_info['why_not_operational'] = unit_status.get('why_not_operational', [])
                    # Only set activities_verbal if present and not Idle
                    activities = unit_status.get('activities_verbal', [])
                    if isinstance(activities, str):
                        activities = [activities]
                    # Filter out Idle and empty values
                    filtered_activities = [a for a in activities if a.strip() and a.strip() != "Idle"]
                    status_info['activities_verbal'] = filtered_activities
                
                units_status.append(status_info)
        
        return render(request, 'dashboard/index.html', {
            'site': site,
            'units_status': units_status,
            'current_site': current_site
        })
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render(request, 'dashboard/index.html', {
            'error': 'Error loading dashboard data'
        })
