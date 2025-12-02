"""
Units views - Unit management and control.
"""
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from mast_utils.permissions import capability_required
from utils.api_proxy import proxy_api_call, proxy_backend
from common.api import ControlApi

logger = logging.getLogger('mast.units')


@login_required
@capability_required('canView')
def unit_list(request):
    """List all units for the current site."""
    try:
        from config import Config
        config = Config()
        
        site = config.local_site
        
        # Get units for this site
        units = []
        if site:
            for unit_id in site.deployed_units:
                unit_name = f"mast{unit_id}"
                try:
                    unit_config = config.get_unit(unit_name)
                    units.append({
                        'name': unit_name,
                        'status': 'deployed',
                        'config': unit_config,
                    })
                except Exception as e:
                    logger.error(f"Error loading unit {unit_name}: {e}")
            
            # Add planned units
            for unit_id in site.planned_units:
                unit_name = f"mast{unit_id}"
                units.append({
                    'name': unit_name,
                    'status': 'planned',
                    'config': None,
                })
        
        context = {
            'units': units,
            'site': site,
            'page_title': 'Units',
        }
        
        return render(request, 'units/list.html', context)
    
    except Exception as e:
        logger.error(f"Error loading units: {e}")
        return render(request, 'units/list.html', {
            'error': 'Error loading units data'
        })


@login_required
@capability_required('canView')
def unit_detail(request, unit_name):
    """Show detailed view of a specific unit."""
    try:
        from config import Config
        config = Config()
        
        unit_config = config.get_unit(unit_name)
        
        context = {
            'unit_name': unit_name,
            'unit_config': unit_config,
            'page_title': f'Unit {unit_name}',
        }
        
        return render(request, 'units/detail.html', context)
    
    except Exception as e:
        logger.error(f"Error loading unit {unit_name}: {e}")
        return render(request, 'units/detail.html', {
            'error': f'Error loading unit {unit_name}'
        })


@proxy_backend
def unit_status(request, unit_name):
    """Get status for a specific unit"""
    api = ControlApi()
    # Return tuple: (api_instance, method_name, args...)
    return (api, 'endpoint_unit_status', unit_name)

# Alternative: Make call directly (proxy_backend validates retroactively)
@proxy_backend  
def unit_power_on(request, unit_name, outlet):
    """Turn on a power outlet"""
    api = ControlApi()
    response = api.endpoint_set_outlet(unit_name, outlet, 'on')
    # Decorator already validated this call is allowed
    return JsonResponse({'success': response.succeeded})
