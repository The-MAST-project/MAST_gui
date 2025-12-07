"""
Registry of backend API endpoints exposed through the GUI.
Only endpoints listed here will be accessible via the GUI.
"""

from dataclasses import dataclass
from typing import Literal

@dataclass
class GuiEndpoint:
    """Definition of a GUI-exposed backend endpoint"""
    service: Literal['control', 'unit', 'spec', 'power', 'safety']
    path: str
    method: Literal['GET', 'POST', 'PUT', 'DELETE']
    requires_capability: str | None = None
    description: str = ""
    
# Control Service Endpoints
CONTROL_ENDPOINTS = [
    GuiEndpoint('control', '/status', 'GET', 'canView', 'Get overall system status'),
    GuiEndpoint('control', '/startup', 'GET', 'canUseControls', 'Start controller'),
    GuiEndpoint('control', '/shutdown', 'GET', 'canUseControls', 'Stop controller'),
]

# Config Service Endpoints
CONFIG_ENDPOINTS = [
    GuiEndpoint('control', '/config/world', 'GET', 'canView', 'Get sites configuration'),
    GuiEndpoint('control', '/config/users', 'GET', 'canChangeUsers', 'Get all users'),
    GuiEndpoint('control', '/config/user', 'GET', 'canView', 'Get specific user'),
    GuiEndpoint('control', '/config/get_unit/{unit_name}', 'GET', 'canView', 'Get unit config'),
    GuiEndpoint('control', '/config/set_unit/{unit_name}', 'POST', 'canChangeConfiguration', 'Set unit config'),
]

# Unit Service Endpoints
UNIT_ENDPOINTS = [
    GuiEndpoint('control', '/unit/{unit_name}/status', 'GET', 'canView', 'Get unit status'),
    GuiEndpoint('control', '/unit/{unit_name}/power_switch/status', 'GET', 'canView', 'Get power switch status'),
    GuiEndpoint('control', '/unit/{unit_name}/power_switch/get_outlet/{outlet_id}', 'GET', 'canView', 'Get outlet state'),
    GuiEndpoint('control', '/unit/{unit_name}/power_switch/set_outlet/{outlet_id}/{state}', 'PUT', 'canUseControls', 'Set outlet state'),
]

# Task Service Endpoints
TASK_ENDPOINTS = [
    GuiEndpoint('control', '/get_tasks', 'GET', 'canView', 'Get all tasks'),
    GuiEndpoint('control', '/execute_assigned_task', 'POST', 'canUseControls', 'Execute a task'),
    GuiEndpoint('control', '/task_acquisition_path_notification', 'PUT', None, 'Internal: Task path notification'),
    GuiEndpoint('control', '/activity_notification', 'PUT', None, 'Internal: Activity notification'),
]

# All registered endpoints
GUI_ENDPOINTS = (
    CONTROL_ENDPOINTS +
    CONFIG_ENDPOINTS +
    UNIT_ENDPOINTS +
    TASK_ENDPOINTS
)

def is_endpoint_allowed(service: str, path: str, method: str) -> bool:
    """Check if an endpoint is allowed to be called from GUI"""
    return any(
        ep.service == service and ep.path == path and ep.method == method
        for ep in GUI_ENDPOINTS
    )

def get_endpoint_capability(service: str, path: str, method: str) -> str | None:
    """Get required capability for an endpoint"""
    for ep in GUI_ENDPOINTS:
        if ep.service == service and ep.path == path and ep.method == method:
            return ep.requires_capability
    return None
