"""
Utilities for generating Django forms from Pydantic models with metadata.
"""
import logging
from typing import Any

logger = logging.getLogger('mast.utils')


def get_field_metadata(pydantic_model, field_name: str) -> dict:
    """Extract UI metadata from Pydantic field."""
    try:
        field_info = pydantic_model.model_fields[field_name]
        return field_info.json_schema_extra or {}
    except (AttributeError, KeyError) as e:
        logger.warning(f"Could not get metadata for field {field_name}: {e}")
        return {}


def is_field_editable(pydantic_model, field_name: str, user) -> bool:
    """Check if user can edit this field based on metadata and permissions."""
    metadata = get_field_metadata(pydantic_model, field_name)
    
    # Check if field is hidden
    if metadata.get('ui.hidden'):
        return False
    
    # Check if field is explicitly marked as not editable
    if not metadata.get('editable', True):
        return False
    
    # Check if user has required capability
    required_cap = metadata.get('required_capability')
    if required_cap:
        mongo_user = getattr(user, 'mongo_user', None)
        if not mongo_user or required_cap not in mongo_user.capabilities:
            return False
    
    return True


def generate_form_fields(pydantic_model, instance, user) -> dict:
    """
    Generate form field definitions from Pydantic model with metadata.
    
    Returns dict of field definitions with UI rendering information.
    """
    fields = {}
    
    for field_name, field_info in pydantic_model.model_fields.items():
        metadata = field_info.json_schema_extra or {}
        
        # Skip hidden fields
        if metadata.get('ui.hidden'):
            continue
        
        # Determine if editable
        editable = is_field_editable(pydantic_model, field_name, user)
        
        # Get validation constraints
        validation = {
            'min': getattr(field_info, 'ge', None) or getattr(field_info, 'gt', None),
            'max': getattr(field_info, 'le', None) or getattr(field_info, 'lt', None),
            'pattern': getattr(field_info, 'pattern', None),
            'required': field_info.is_required(),
        }
        
        fields[field_name] = {
            'name': field_name,
            'value': getattr(instance, field_name, None),
            'editable': editable,
            'description': field_info.description or field_name.replace('_', ' ').title(),
            'widget': metadata.get('ui.widget', 'text'),
            'unit': metadata.get('ui.unit'),
            'format': metadata.get('ui.format'),
            'group': metadata.get('ui.group', 'General'),
            'validation': validation,
            'error_message': metadata.get('error_message', f'Invalid {field_name}'),
            'tooltip': metadata.get('tooltip', field_info.description),
        }
    
    return fields


def group_fields(fields: dict) -> dict:
    """Group fields by their ui.group metadata."""
    grouped = {}
    for field in fields.values():
        group = field['group']
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(field)
    return grouped
