from django import template
from views.urls import get_dynamic_static_url as _get_dynamic_static_url
from views.urls import get_dynamic_url as _get_dynamic_url

register = template.Library()

@register.simple_tag(takes_context=True)
def get_dynamic_static_url(context, static_path):
    # SET BREAKPOINT HERE
    request = context['request']
    return _get_dynamic_static_url(request, static_path)

@register.simple_tag(takes_context=True)
def get_dynamic_url(context, viewname, *args, **kwargs):
    # SET BREAKPOINT HERE
    request = context['request']
    return _get_dynamic_url(request, viewname, *args, **kwargs)
