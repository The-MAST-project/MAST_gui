"""
Views for unit management and monitoring
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from common.config import Config
from common.api import ControllerApi
from common.dlipowerswitch import PowerSwitchStatus
from common.models.statuses import UnitStatus, ShortUnitStatus, FullUnitStatus
import asyncio
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
import os
from pathlib import Path
import mimetypes


@login_required
def units_list(request):
    """
    Units page - shows all units for selected site with selector
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
            response = asyncio.run(controller.client.get(f"unit/{unit_id}/status"))
            
            operational_status = 'unknown'
            if response.succeeded and response.value:
                # response.value is discriminated union UnitStatus
                unit_status: UnitStatus = response.value
                
                if isinstance(unit_status, ShortUnitStatus):
                    # Controller couldn't reach unit
                    operational_status = 'operational' if unit_status.operational else 'offline'
                elif isinstance(unit_status, FullUnitStatus):
                    # Full status from unit
                    operational_status = 'operational' if unit_status.operational else 'error'
            
            unit_data = {
                'name': unit_id,
                'full_name': unit_id,
                'deployed': unit_id in site.deployed_units,
                'status': operational_status,
                'status_text': status_text,
                'building': display_name
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
    
    return render(request, 'units/list.html', {
        'buildings': buildings_sorted,
        'site': site
    })


@login_required
def unit_detail(request, unit_name):
    """
    Unit detail page - shows power supply and component accordion
    """
    # Get current site from session
    current_site = request.session.get('selected_site', 'wis')
    
    # Check if user has control permissions
    user_can_control = request.user.has_perm('auth.canUseControls')
    
    # Get unit status from ControllerApi (for unit operational info)
    controller = ControllerApi(site_name=current_site)
    status_response = asyncio.run(controller.client.get(f"unit/{unit_name}/status"))
    
    unit_operational = False
    unit_info = {}
    component_statuses = {}
    
    if status_response.succeeded and status_response.value:
        # response.value is discriminated union UnitStatus
        unit_status = ShortUnitStatus(**status_response.value) if status_response.value['type'] == 'short' else FullUnitStatus(**status_response.value)
        
        if isinstance(unit_status, ShortUnitStatus):
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
    power_response = asyncio.run(controller.client.get(f"unit/{unit_name}/power_switch/status"))
    
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
    
    return render(request, 'units/detail.html', {
        'unit_name': unit_name,
        'site': current_site,
        'outlets': outlets,
        'unit_operational': unit_operational,
        'unit_info': unit_info,
        'component_statuses': component_statuses,  # Pass component data to template
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
        controller.client.put(f"unit/{unit_name}/power_switch/set_outlet/{outlet_id}/toggle")
    )
    
    if not response.succeeded:
        return JsonResponse({'error': 'Failed to toggle outlet'}, status=500)
    
    # response.value contains the new state (bool or None)
    if response.value is None:
        new_state = 'unknown'
    else:
        new_state = 'on' if response.value else 'off'
    
    # Get power switch status to get outlet name
    power_response = asyncio.run(controller.client.get(f"unit/{unit_name}/power_switch/status"))
    
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

# Use os.path for cross-platform compatibility

def get_image_path(filename):
    # Use Path for better cross-platform support
    return Path(settings.MEDIA_ROOT) / 'images' / filename.lower()
