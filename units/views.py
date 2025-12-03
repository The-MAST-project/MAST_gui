"""
Views for unit management and monitoring
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from common.config import Config
from common.api import ControllerApi
from common.dlipowerswitch import PowerSwitchStatus
import asyncio
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


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
            
            # Get unit status from controller API (TODO: implement)
            unit_data = {
                'name': unit_id,
                'full_name': unit_id,
                'deployed': unit_id in site.deployed_units,
                'status': 'unknown',  # TODO: fetch from API
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
    
    # Get power switch status from ControllerApi
    controller = ControllerApi()
    response = asyncio.run(controller.client.get(f"unit/{unit_name}/power_switch/status"))
    
    outlets = []
    if response.succeeded and response.value:
        # response.value is PowerSwitch status with outlets list
        power_switch_status: PowerSwitchStatus = PowerSwitchStatus(**response.value)
        
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
                'can_control': user_can_control and not is_computer,  # Disable Computer outlet
                'is_computer': is_computer  # Flag for special handling
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
    })


@login_required
@require_http_methods(["POST"])
def toggle_outlet(request, unit_name, outlet_id):
    """
    Toggle power outlet state via ControllerApi
    """
    # Check if user has control permissions
    if not request.user.has_perm('auth.canUseControls'):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Toggle the outlet
    controller = ControllerApi()
    response = asyncio.run(
        controller.client.put(f"unit/{unit_name}/power_switch/set_outlet/{outlet_id}/toggle")
    )
    
    if not response.succeeded:
        return JsonResponse({'error': 'Failed to toggle outlet'}, status=500)
    
    # Get updated outlet state - returns bool | None
    status_response = asyncio.run(
        controller.client.get(f"unit/{unit_name}/power_switch/get_outlet/{outlet_id}")
    )
    
    if status_response.succeeded:
        # Convert boolean to 'on'/'off' string, None to 'unknown'
        if status_response.value is None:
            new_state = 'unknown'
        else:
            new_state = 'on' if status_response.value else 'off'
        
        return JsonResponse({
            'status': new_state,
            'outlet_id': outlet_id
        })
    
    return JsonResponse({'error': 'Failed to get outlet state'}, status=500)
