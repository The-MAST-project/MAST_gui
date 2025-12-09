"""
Utilities for extracting and processing Pydantic configuration schemas
"""
from pydantic import BaseModel
from typing import Dict, Any


def extract_field_metadata(model_class: type[BaseModel]) -> Dict[str, Any]:
    """
    Extract field metadata from Pydantic model for client-side validation.
    
    Returns dict with field name as key and metadata dict as value.
    """
    fields_meta = {}
    
    for field_name, field_info in model_class.model_fields.items():
        meta = {
            'label': field_info.json_schema_extra.get('ui', {}).get('label', field_name),
            'name': field_name,
            'type': get_type_name(field_info.annotation),
            'default': field_info.default if field_info.default is not None else '',
            'required': field_info.is_required(),
        }
        
        # Extract validation constraints from metadata
        if field_info.metadata:
            for constraint in field_info.metadata:
                extract_constraint(constraint, meta)
        
        # Extract custom UI metadata from json_schema_extra
        if field_info.json_schema_extra:
            meta.update(field_info.json_schema_extra)
        
        # Build error message if not provided
        if 'error_message' not in meta:
            meta['error_message'] = build_default_error_message(meta)
        
        fields_meta[field_name] = meta
    
    return fields_meta


def get_type_name(annotation) -> str:
    """Extract clean type name from annotation"""
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    return str(annotation).replace('typing.', '')


def extract_constraint(constraint, meta: dict):
    """Extract validation constraints from Pydantic metadata"""
    if hasattr(constraint, 'ge'):
        meta['min'] = constraint.ge
    if hasattr(constraint, 'le'):
        meta['max'] = constraint.le
    if hasattr(constraint, 'gt'):
        meta['min'] = constraint.gt + 0.01
    if hasattr(constraint, 'lt'):
        meta['max'] = constraint.lt - 0.01
    if hasattr(constraint, 'min_length'):
        meta['minLength'] = constraint.min_length
    if hasattr(constraint, 'max_length'):
        meta['maxLength'] = constraint.max_length
    if hasattr(constraint, 'pattern'):
        meta['pattern'] = constraint.pattern


def build_default_error_message(meta: dict) -> str:
    """Generate default error message from constraints"""
    if meta.get('required'):
        return f"{meta['name']} is required"
    
    if 'min' in meta and 'max' in meta:
        unit = meta.get('ui.unit', '')
        return f"Must be between {meta['min']} and {meta['max']} {unit}".strip()
    elif 'min' in meta:
        return f"Must be >= {meta['min']}"
    elif 'max' in meta:
        return f"Must be <= {meta['max']}"
    
    if 'pattern' in meta:
        return "Invalid format"
    
    return "Invalid value"
