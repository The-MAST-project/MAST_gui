"""
Template filters for time display.
"""
from django import template
from datetime import datetime

register = template.Library()


@register.filter
def seconds_since(value):
    """
    Returns the number of seconds since the given datetime.
    
    Args:
        value: datetime object
    
    Returns:
        String like "45 seconds" or "3 seconds"
    """
    if not value:
        return ""
    
    now = datetime.now(tz=value.tzinfo) if value.tzinfo else datetime.now()
    delta = now - value
    seconds = int(delta.total_seconds())
    
    if seconds == 1:
        return "1 second"
    else:
        return f"{seconds} seconds"
