"""
Template filters for displaying activity flags as badges.
"""
from django import template
from common.activities import MountActivities, FocuserActivities, StageActivities, CoverActivities, ImagerActivities

register = template.Library()


@register.filter
def activity_badge_class(activity_name: str) -> str:
    """
    Returns Bootstrap badge class based on activity type.
    
    Args:
        activity_name: Name of the activity (e.g., "Slewing", "Tracking")
    
    Returns:
        Bootstrap badge class string
    """
    # Handle different activity name formats
    # Could be "MountActivities.Slewing" or just "Slewing"
    if ':' in activity_name:
        activity_name = activity_name.split(':')[0].strip()
    if '.' in activity_name:
        # Extract just the activity name after the dot
        activity_name = activity_name.split('.')[-1]
    
    # Map activity names to badge colors
    activity_colors = {
        # Mount activities
        'Slewing': 'warning',
        'Tracking': 'success',
        'Parking': 'info',
        'StartingUp': 'primary',
        'ShuttingDown': 'secondary',
        'FindingHome': 'info',
        'Moving': 'warning',
        'Dancing': 'warning',
        
        # Focuser activities
        'Moving': 'warning',
        
        # Cover activities
        'Opening': 'primary',
        'Closing': 'secondary',
        
        # Imager activities
        'Exposing': 'success',
        'CoolingDown': 'info',
        'WarmingUp': 'warning',
        'ReadingOut': 'primary',
        'Saving': 'info',
        
        # Stage activities
        'Homing': 'info',
        
        # Special cases
        'Idle': 'secondary',
    }
    
    return f"bg-{activity_colors.get(activity_name, 'secondary')}"


@register.filter
def format_activity_name(activity_name: str) -> str:
    """
    Formats activity name for display (adds spaces before capitals).
    
    Args:
        activity_name: CamelCase activity name (could be "Activity.Idle: 0" or just "Idle")
    
    Returns:
        Formatted string with spaces
    """
    import re
    
    # Remove everything after ':' (e.g., "<Activity.Idle: 0>" -> "<Activity.Idle")
    if ':' in activity_name:
        activity_name = activity_name.split(':')[0].strip()
    
    # Remove angle brackets if present (e.g., "<Activity.Idle" -> "Activity.Idle")
    activity_name = activity_name.strip('<>').strip()
    
    # Handle different activity name formats
    # Could be "MountActivities.Slewing" or just "Slewing"
    if ':' in activity_name:
        activity_name = activity_name.split(':')[0].strip()
    if '.' in activity_name:
        # Extract just the activity name after the dot
        activity_name = activity_name.split('.')[-1]
    
    # Special case for Idle
    if activity_name == 'Idle':
        return 'Idle'
    
    # Add space before capital letters (except first)
    formatted = re.sub(r'(?<!^)(?=[A-Z])', ' ', activity_name)
    return formatted


@register.filter
def format_state_name(state_name: str) -> str:
    """
    Formats state name by extracting just the state from enum notation.
    
    Args:
        state_name: State name (could be "<CoverState.Open: 1>" or just "Open")
    
    Returns:
        Formatted state name
    """
    if not state_name:
        return ""
    
    # Remove everything after ':' (e.g., "<CoverState.Open: 1>" -> "<CoverState.Open")
    if ':' in state_name:
        state_name = state_name.split(':')[0].strip()
    
    # Remove angle brackets if present (e.g., "<CoverState.Open" -> "CoverState.Open")
    state_name = state_name.strip('<>').strip()
    
    # Handle different formats
    # Could be "CoverState.Open" or just "Open"
    if '.' in state_name:
        # Extract just the state name after the dot
        state_name = state_name.split('.')[-1]
    
    return state_name
