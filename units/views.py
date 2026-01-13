"""
Views for unit management and monitoring
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from common.config import Config
from common.api import ControllerApi
from common.dlipowerswitch import PowerSwitchStatus
from common.models.statuses import UnitStatus, ShortStatus, FullUnitStatus
import asyncio
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
import datetime
from pathlib import Path
import mimetypes
import json
import logging

from .config_utils import extract_field_metadata
from common.config.focuser import FocuserConfig

# Set default log level to DEBUG for this module
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@login_required
def units_list(request):
    """
    Units page - shows all units for selected site with selector
    Periodic refresh of unit status is handled client-side via JS polling.
    """
    # Get current site from session
    current_site = request.session.get('selected_site', 'wis')
    
    # Get site configuration from MongoDB
    config = Config()
    sites = config.get_sites()
    
    # Find the selected site
    site = None
    for s in sites:
        if s.name == current_site:
            site = s
            break
    
    if not site:
        return render(request, 'units/list.html', {
            'error': f'Site {current_site} not found',
            'units': [],
            'buildings': {}
        })
    
    # Organize units by building
    buildings_data = {}
    
    # site.buildings is a list[Building]
    for building in site.buildings:
        building_name = building.names[0] if building.names else "Unknown"
        # Prepend 'Enclosure' to building name
        display_name = f"Enclosure: {building_name}"
        buildings_data[display_name] = {
            'name': display_name,
            'units': [],
            'sort_order': 0 if 'clamshell' in building_name.lower() else 1  # Clamshell first
        }
        
        # building.units is a list[str] (unit IDs)
        for unit_id in building.units:
            # Determine status text
            if unit_id in site.deployed_units:
                status_text = 'Deployed'
            elif unit_id in site.units_in_maintenance:
                status_text = 'In Maintenance'
            else:
                status_text = 'Planned'
            
            # Get unit status from controller API using discriminated union
            controller = ControllerApi(site_name=current_site)
            response = asyncio.run(controller.client.get(f"unit/{current_site}/{unit_id}/status"))
            
            operational_status = 'unknown'
            activities_verbal = []
            if response.succeeded and response.value:
                unit_status: UnitStatus = response.value
                if isinstance(unit_status, ShortStatus):
                    # Controller couldn't reach unit
                    operational_status = 'operational' if unit_status.operational else 'offline'
                    activities_verbal = getattr(unit_status, 'activities_verbal', []) or []
                    if isinstance(activities_verbal, str):
                        activities_verbal = [activities_verbal]
                elif isinstance(unit_status, FullUnitStatus):
                    # Full status from unit
                    operational_status = 'operational' if unit_status.operational else 'error'
                    activities_verbal = getattr(unit_status, 'activities_verbal', []) or []
                    if isinstance(activities_verbal, str):
                        activities_verbal = [activities_verbal]
            
            unit_data = {
                'name': unit_id,
                'full_name': unit_id,
                'deployed': unit_id in site.deployed_units,
                'status': operational_status,
                'status_text': status_text,
                'building': display_name,
                'activities_verbal': activities_verbal,
            }
            buildings_data[display_name]['units'].append(unit_data)
        
        # Sort units for proper display order (upper right to lower left, alternating)
        # For North/South: units numbered 1,3,5,7,9 (row 1) and 2,4,6,8,10 (row 2)
        # Display order: 9,7,5,3,1 (row 1 right to left), then 10,8,6,4,2 (row 2 right to left)
        if len(buildings_data[display_name]['units']) > 1:
            # Extract numeric part from unit names for sorting
            units = buildings_data[display_name]['units']
            # Separate odd and even units
            odd_units = [u for u in units if int(u['name'].replace(site.project, '')) % 2 == 1]
            even_units = [u for u in units if int(u['name'].replace(site.project, '')) % 2 == 0]
            # Sort each row descending (right to left)
            odd_units.sort(key=lambda u: int(u['name'].replace(site.project, '')), reverse=True)
            even_units.sort(key=lambda u: int(u['name'].replace(site.project, '')), reverse=True)
            # Store in display order with row split
            buildings_data[display_name]['row1'] = odd_units
            buildings_data[display_name]['row2'] = even_units
            buildings_data[display_name]['units'] = odd_units + even_units
    
    # Sort buildings: clamshell first, then others
    buildings_sorted = dict(sorted(buildings_data.items(), key=lambda x: x[1]['sort_order']))
    
    # Get site status from cache
    from MAST_gui.context_processors import _MAST_CACHE
    sites_status = _MAST_CACHE.get('status')
    
    # Prepare instrument room components
    instrument_room = {
        'deepspec': None,
        'highspec': None,
        'controller': None,
    }
    
    if sites_status and hasattr(sites_status, 'sites') and current_site in sites_status.sites:
        site_status = sites_status.sites[current_site]
        
        # Get each component's status
        for comp_name in ['deepspec', 'highspec', 'controller']:
            comp_status = getattr(site_status, comp_name, None)
            # Format display name
            if comp_name == 'deepspec':
                display_name = 'Deepspec'
            elif comp_name == 'highspec':
                display_name = 'Highspec'
            else:
                display_name = 'Controller'
            
            instrument_room[comp_name] = {
                'name': comp_name,
                'display_name': display_name,
                'detected': False if comp_status is None else getattr(comp_status, 'detected', False),
                # 'activities_verbal': ['Unknown'] if comp_status is None else getattr(comp_status, 'activities_verbal', []) or [],
            }
    
    return render(request, 'units/list.html', {
        'buildings': buildings_sorted,
        'site': site,
        'instrument_room': instrument_room,
    })


@login_required
def unit_detail(request, unit_name):
    """
    Unit detail page - shows power supply and component accordion
    """
    # Get current site from session
    current_site = request.session.get('selected_site', 'wis')
    
    # --- Find building name for this unit ---
    config = Config()
    sites = config.get_sites()
    site_obj = next((s for s in sites if s.name == current_site), None)
    building_name = None
    if site_obj:
        for building in getattr(site_obj, 'buildings', []):
            if unit_name in getattr(building, 'units', []):
                building_name = building.names[0] if getattr(building, 'names', []) else "Unknown"
                break

    # Check if user has control permissions
    user_can_control = request.user.has_perm('auth.canUseControls')
    
    # Get unit status from ControllerApi (for unit operational info)
    controller = ControllerApi(site_name=current_site)
    status_response = asyncio.run(controller.client.get(f"unit/{current_site}/{unit_name}/status"))
    
    unit_operational = False
    unit_info = {}
    component_statuses = {}
    
    if status_response.succeeded and status_response.value:
        # response.value is discriminated union UnitStatus
        # logger.info(f"Unit {unit_name} status response: {status_response.value}")
        unit_status = ShortStatus(**status_response.value) if status_response.value['type'] == 'short' else FullUnitStatus(**status_response.value)
        
        if isinstance(unit_status, ShortStatus):
            # Controller couldn't reach unit - show limited info
            unit_operational = unit_status.operational
            unit_info = {
                'type': 'short',
                'powered': unit_status.powered,
                'detected': unit_status.detected,
                'operational': unit_status.operational
            }
        
        elif isinstance(unit_status, FullUnitStatus):
            # Full status from unit - use all available data
            unit_operational = unit_status.operational
            
            # Convert activities_verbal to list if it's a string
            activities_list = unit_status.activities_verbal or []
            if isinstance(activities_list, str):
                # If it's a single string, wrap it in a list
                activities_list = [activities_list]
            
            unit_info = {
                'type': 'full',
                'powered': unit_status.powered,
                'detected': unit_status.detected,
                'operational': unit_status.operational,
                'guiding': unit_status.guiding,
                'autofocusing': unit_status.autofocusing,
                'activities_verbal': activities_list,  # Now guaranteed to be a list
                'why_not_operational': unit_status.why_not_operational or []
            }
            
            # Extract component statuses from full status
            if unit_status.mount:
                # Convert mount activities to list as well
                mount_activities = unit_status.activities_verbal or []
                if isinstance(mount_activities, str):
                    mount_activities = [mount_activities]
                
                component_statuses['mount'] = {
                    'powered': unit_status.mount.powered,
                    'detected': unit_status.mount.detected,
                    'operational': unit_status.mount.operational,
                    'tracking': unit_status.mount.tracking,
                    'slewing': unit_status.mount.slewing,
                    'ra_j2000_hours': unit_status.mount.ra_j2000_hours,
                    'dec_j2000_degs': unit_status.mount.dec_j2000_degs,
                    'target_verbal': unit_status.mount.target_verbal,
                    'activities_verbal': mount_activities  # Guaranteed to be a list
                }
            
            if unit_status.imager:
                imager_activities = getattr(unit_status.imager, 'activities_verbal', None) or []
                if isinstance(imager_activities, str):
                    imager_activities = [imager_activities]
                
                component_statuses['imager'] = {
                    'powered': getattr(unit_status.imager, 'powered', None),
                    'detected': getattr(unit_status.imager, 'detected', None),
                    'operational': unit_status.imager.operational,
                    'activities_verbal': imager_activities,
                    'why_not_operational': getattr(unit_status.imager, 'why_not_operational', [])
                }
            
            if unit_status.focuser:
                focuser_activities = unit_status.activities_verbal or []
                if isinstance(focuser_activities, str):
                    focuser_activities = [focuser_activities]
                
                component_statuses['focuser'] = {
                    'powered': unit_status.focuser.powered,
                    'detected': unit_status.focuser.detected,
                    'operational': unit_status.focuser.operational,
                    'position': unit_status.focuser.position,
                    'target': unit_status.focuser.target,
                    'target_verbal': unit_status.focuser.target_verbal,
                    'moving': unit_status.focuser.moving,
                    'activities_verbal': focuser_activities
                }
            
            if unit_status.stage:
                stage_activities = unit_status.activities_verbal or []
                if isinstance(stage_activities, str):
                    stage_activities = [stage_activities]
                
                component_statuses['stage'] = {
                    'powered': unit_status.stage.powered,
                    'detected': unit_status.stage.detected,
                    'operational': unit_status.stage.operational,
                    'position': unit_status.stage.position,
                    'at_preset': unit_status.stage.at_preset,
                    'target_verbal': unit_status.stage.target_verbal,
                    'activities_verbal': stage_activities
                }
            
            if unit_status.covers:
                covers_activities = unit_status.activities_verbal or []
                if isinstance(covers_activities, str):
                    covers_activities = [covers_activities]
                
                component_statuses['covers'] = {
                    'powered': unit_status.covers.powered,
                    'detected': unit_status.covers.detected,
                    'operational': unit_status.covers.operational,
                    'state': unit_status.covers.state.name if unit_status.covers.state else None,
                    'state_verbal': unit_status.covers.state_verbal,
                    'target_verbal': unit_status.covers.target_verbal,
                    'activities_verbal': covers_activities
                }
            
            if unit_status.guider:
                guider_activities = unit_status.guider.activities_verbal or []
                if isinstance(guider_activities, str):
                    guider_activities = [guider_activities]
                
                component_statuses['guider'] = {
                    'activities': unit_status.guider.activities,
                    'activities_verbal': guider_activities,
                    'backend': unit_status.guider.backend.model_dump() if unit_status.guider.backend else None
                }
    
    # Always get power switch status from controller endpoint
    # (separate from unit status, works even when unit not operational)
    power_response = asyncio.run(controller.client.get(f"unit/{current_site}/{unit_name}/power_switch/status"))
    
    outlets = []
    if power_response.succeeded and power_response.value:
        # power_response.value is PowerSwitchStatus with outlets list
        power_switch_status: PowerSwitchStatus = PowerSwitchStatus(**power_response.value)
        
        # power_switch_status.outlets is a list of outlet objects with name and state
        for outlet in power_switch_status.outlets:
            # Use outlet.id if available, otherwise use the name
            outlet_id = getattr(outlet, 'id', outlet.name)
            
            # Computer outlet cannot be toggled - must use Unit controls
            is_computer = outlet.name.lower() == 'computer'
            
            outlets.append({
                'id': outlet_id,  # Keep original ID from backend
                'name': outlet.name,  # Display name
                'status': 'on' if outlet.state else 'off',
                'can_control': user_can_control and not is_computer,
                'is_computer': is_computer
            })
    else:
        # Handle error - use generic outlet names with unknown status
        for i in range(8):
            outlets.append({
                'id': f'outlet{i+1}',
                'name': f'Outlet {i+1}',
                'status': 'unknown',
                'can_control': False,
                'is_computer': False
            })
    
    # --- Fetch unit configuration from ControllerApi ---
    focuser_config_values = {}
    focuser_config_schema = {}
    unit_config_focuser = ""
    unit_config_dump = ""

    controller = ControllerApi(site_name=current_site)
    config_response = asyncio.run(
        controller.client.get(f"config/get_unit/{unit_name}")
    )

    if config_response.succeeded and config_response.value:
        unit_config = config_response.value
        # Dump the whole unit config for debugging
        try:
            import pprint
            unit_config_dump = pprint.pformat(unit_config)
        except Exception:
            unit_config_dump = str(unit_config)

        # Try to extract focuser config robustly
        focuser_obj = None
        # If unit_config is a dict, try key lookup
        if isinstance(unit_config, dict):
            focuser_obj = unit_config.get('focuser', None)
        else:
            # Try attribute access
            focuser_obj = getattr(unit_config, 'focuser', None)
            # If still None, try dict conversion
            if focuser_obj is None and hasattr(unit_config, '__dict__'):
                focuser_obj = unit_config.__dict__.get('focuser', None)

        unit_config_focuser = str(focuser_obj)
        if focuser_obj:
            if hasattr(focuser_obj, 'model_dump'):
                focuser_config_values = focuser_obj.model_dump()
            elif hasattr(focuser_obj, 'dict'):
                focuser_config_values = focuser_obj.dict()
            elif isinstance(focuser_obj, dict):
                focuser_config_values = focuser_obj
            else:
                # Last resort: try __dict__
                focuser_config_values = getattr(focuser_obj, '__dict__', {})
            focuser_config_schema = extract_field_metadata(FocuserConfig)

    # print(f"unit_details: {focuser_config_values=}\n{focuser_config_schema=}")
    return render(request, 'units/detail.html', {
        'unit_name': unit_name,
        'site': current_site,
        'building_name': building_name,
        'outlets': outlets,
        'unit_operational': unit_operational,
        'unit_info': unit_info,
        'component_statuses': component_statuses,
        'focuser_config_values': json.dumps(focuser_config_values),
        'focuser_config_schema': json.dumps(focuser_config_schema),
        'unit_config_focuser': unit_config_focuser,
        'unit_config_dump': unit_config_dump,
    })


@login_required
@require_http_methods(["POST"])
def toggle_outlet(request, unit_name, outlet_id):
    """
    Toggle power outlet state via ControllerApi
    Uses /unit/{unit_name}/power_switch/set_outlet/{outlet_id}/toggle endpoint
    """
    # Check if user has control permissions
    if not request.user.has_perm('auth.canUseControls'):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Get current site from session
    current_site = request.session.get('selected_site', 'wis')
    
    # Toggle the outlet using controller endpoint
    # Returns the new state directly
    controller = ControllerApi(site_name=current_site)
    response = asyncio.run(
        controller.client.put(f"unit/{current_site}/{unit_name}/power_switch/set_outlet/{outlet_id}/toggle")
    )
    
    if not response.succeeded:
        return JsonResponse({'error': 'Failed to toggle outlet'}, status=500)
    
    # response.value contains the new state (bool or None)
    if response.value is None:
        new_state = 'unknown'
    else:
        new_state = 'on' if response.value else 'off'
    
    # Get power switch status to get outlet name
    power_response = asyncio.run(controller.client.get(f"unit/{current_site}/{unit_name}/power_switch/status"))
    
    if power_response.succeeded and power_response.value:
        power_switch_status = PowerSwitchStatus(**power_response.value)
        
        # Find the outlet that was toggled
        outlet = None
        for o in power_switch_status.outlets:
            if getattr(o, 'id', o.name) == outlet_id:
                outlet = o
                break
        
        if outlet:
            is_computer = outlet.name.lower() == 'computer'
            user_can_control = request.user.has_perm('auth.canUseControls')
            
            # Return the complete outlet HTML for swap
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            
            html = render_to_string('units/components/outlet_button.html', {
                'outlet': {
                    'id': outlet_id,
                    'name': outlet.name,
                    'status': new_state,
                    'can_control': user_can_control and not is_computer,
                    'is_computer': is_computer
                },
                'unit_name': unit_name
            })
            
            return HttpResponse(html)
    
    return JsonResponse({'error': 'Failed to get outlet info'}, status=500)


@login_required
@require_http_methods(["POST"])
def save_component_config(request, unit_name, component):
    """
    Save component configuration via ControllerApi
    """
    # Check if user has configuration permission
    if not request.user.has_perm('auth.canChangeConfiguration'):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Get current site from session
    current_site = request.session.get('selected_site', 'wis')
    
    try:
        # Parse request body
        config_data = json.loads(request.body)
        
        # Get current unit config
        controller = ControllerApi(site_name=current_site)
        get_response = asyncio.run(
            controller.client.get(f"config/get_unit/{unit_name}")
        )
        
        if not get_response.succeeded:
            return JsonResponse({'error': 'Failed to get current config'}, status=500)
        
        # Update the specific component config
        unit_config = get_response.value
        
        if component == 'focuser' and hasattr(unit_config, 'focuser'):
            # Validate with Pydantic
            from common.config.focuser import FocuserConfig
            updated_focuser = FocuserConfig(**config_data)
            unit_config.focuser = updated_focuser
        else:
            return JsonResponse({'error': f'Unknown component: {component}'}, status=400)
        
        # Save via ControllerApi
        save_response = asyncio.run(
            controller.client.post(f"config/set_unit/{unit_name}", json=unit_config.model_dump())
        )
        
        if save_response.succeeded:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': save_response.errors}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# @login_required
# def controller_status_check(request):
#     """
#     Endpoint for polling controller status.
#     Returns basic health/status info for the controller.
#     """
#     # You can expand this with real health checks as needed
#     status = {
#         "controller": "online",
#         "message": "Controller is running",
#         "timestamp": str(datetime.datetime.utcnow()),
#     }
#     return JsonResponse(status)