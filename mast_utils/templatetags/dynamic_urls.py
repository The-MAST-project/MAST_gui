from django import template
from django.core.exceptions import ImproperlyConfigured

# Import get_dynamic_url from the correct location, but alias to avoid recursion
try:
    from views.urls import get_dynamic_url as get_dynamic_url_util
except ImportError as e:
    raise ImproperlyConfigured("Could not import get_dynamic_url from views.urls") from e

register = template.Library()


@register.simple_tag(takes_context=True)
def get_dynamic_url(context, viewname, *args, **kwargs):
    """
    Usage: {% get_dynamic_url 'viewname' arg1 arg2 kwarg1='val' %}
    """
    request = context.get("request")
    if not request:
        return ""
    return get_dynamic_url_util(request, viewname, *args, **kwargs)


# Dynamic static URL support
try:
    from views.urls import get_dynamic_static_url as get_dynamic_static_url_util
except ImportError as e:
    raise ImproperlyConfigured("Could not import get_dynamic_static_url from views.urls") from e


@register.simple_tag(takes_context=True)
def get_dynamic_static_url(context, static_path):
    """
    Usage: {% get_dynamic_static_url 'css/style.css' %}
    """
    request = context.get("request")
    if not request:
        return ""
    return get_dynamic_static_url_util(request, static_path)
