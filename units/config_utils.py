"""
Utilities for extracting and processing Pydantic configuration schemas
"""
import typing
from pydantic import BaseModel
from typing import Dict, Any

try:
    from pydantic_core import PydanticUndefinedType as _PydanticUndefinedType
except ImportError:
    _PydanticUndefinedType = type(None)  # fallback: never matches


def extract_field_metadata(model_class: type[BaseModel]) -> Dict[str, Any]:
    """
    Extract flat field metadata from a Pydantic model (no recursion into nested models).
    Returns dict with field name as key and metadata dict as value.
    """
    return {
        field_name: _field_meta(field_name, field_info)
        for field_name, field_info in model_class.model_fields.items()
    }


def _unwrap_base_model(annotation) -> type[BaseModel] | None:
    """
    If annotation is (or wraps) a BaseModel subclass, return that class.
    Handles Optional[Model] (typing.Union and Python 3.10+ X | None) transparently.
    Returns None for scalars, lists, dicts, and other non-model types.
    """
    import types as _types
    origin = typing.get_origin(annotation)

    # typing.Optional[X] / typing.Union[X, None]
    if origin is typing.Union:
        inner_args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(inner_args) == 1:
            annotation = inner_args[0]
        else:
            return None  # real Union of multiple types — treat as scalar

    # Python 3.10+ pipe syntax: X | None  (types.UnionType)
    elif hasattr(_types, 'UnionType') and isinstance(annotation, _types.UnionType):
        inner_args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(inner_args) == 1:
            annotation = inner_args[0]
        else:
            return None

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _safe_default(field_info):
    """Return a JSON-safe default value for the field."""
    v = field_info.default
    if v is None or isinstance(v, _PydanticUndefinedType):
        return ''
    if isinstance(v, (str, int, float, bool)):
        return v
    return ''


def _field_meta(field_name, field_info) -> Dict[str, Any]:
    """Extract metadata for a single scalar field."""
    meta = {
        'label': field_name,
        'name': field_name,
        'type': get_type_name(field_info.annotation),
        'default': _safe_default(field_info),
        'required': field_info.is_required(),
    }

    if field_info.metadata:
        for constraint in field_info.metadata:
            extract_constraint(constraint, meta)

    if field_info.json_schema_extra:
        # Promote ui hints to top level so JS can access field.widget, field.unit, etc.
        ui = field_info.json_schema_extra.get('ui', {})
        meta.update(ui)
        if 'label' in ui:
            meta['label'] = ui['label']

    if 'error_message' not in meta:
        meta['error_message'] = build_default_error_message(meta)

    return meta


def extract_field_metadata_recursive(model_class: type[BaseModel]) -> Dict[str, Any]:
    """
    Recursively extract field metadata from a Pydantic model.

    Fields whose type is a BaseModel subclass (or Optional[BaseModel]) produce a
    group entry with ``_is_group: True`` and a ``fields`` sub-dict — these map to
    card categories in the plan form.  All other fields are extracted as flat
    scalar metadata dicts.
    """
    result: Dict[str, Any] = {}

    for field_name, field_info in model_class.model_fields.items():
        nested = _unwrap_base_model(field_info.annotation)
        if nested is not None:
            ui = (field_info.json_schema_extra or {}).get('ui', {})
            result[field_name] = {
                '_is_group': True,
                'label': ui.get('label', field_name.replace('_', ' ').title()),
                'fields': extract_field_metadata_recursive(nested),
            }
        else:
            result[field_name] = _field_meta(field_name, field_info)

    return result


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
        return f"Must be in range [{meta['min']}..{meta['max']}] {unit}".strip()
    elif 'min' in meta:
        return f"Must be >= {meta['min']}"
    elif 'max' in meta:
        return f"Must be <= {meta['max']}"
    
    if 'pattern' in meta:
        return f"Pattern violation '{meta['pattern']}'"
    
    return "Invalid value"
