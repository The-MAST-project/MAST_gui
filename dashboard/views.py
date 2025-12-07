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
        
        # Get site configuration
        config = Config()
        sites = config.get_sites()
        site = next((s for s in sites if s.name == current_site), None)
        
        if not site:
            return render(request, 'dashboard/index.html', {
                'error': f'Site {current_site} not found'
            })
        
        # Get unit statuses using discriminated union
        controller = ControllerApi(site_name=current_site)
        units_status = []
        
        for building in site.buildings:
            for unit_id in building.units:
                response = asyncio.run(controller.client.get(f"unit/{unit_id}/status"))
                
                status_info = {
                    'name': unit_id,
                    'building': building.names[0] if building.names else "Unknown",
                    'status': 'unknown',
                    'deployed': unit_id in site.deployed_units
                }
                
                if response.succeeded and response.value:
                    unit_status: UnitStatus = response.value
                    
                    if isinstance(unit_status, ShortUnitStatus):
                        # Controller couldn't reach unit
                        status_info['status'] = 'operational' if unit_status.operational else 'offline'
                        status_info['powered'] = unit_status.powered
                        status_info['detected'] = unit_status.detected
                        
                    elif isinstance(unit_status, FullUnitStatus):
                        # Full status from unit
                        status_info['status'] = 'operational' if unit_status.operational else 'error'
                        status_info['powered'] = unit_status.powered
                        status_info['detected'] = unit_status.detected
                        status_info['guiding'] = unit_status.guiding
                        status_info['autofocusing'] = unit_status.autofocusing
                        status_info['why_not_operational'] = unit_status.why_not_operational or []
                        status_info['activities_verbal'] = unit_status.activities_verbal or []
                
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
