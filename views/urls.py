from MAST_common.proxy import ProxyContext


def get_dynamic_url(request, viewname, *args, **kwargs):
    """Resolve a URL name to a fully-qualified proxy-aware URL."""
    return ProxyContext.from_request(request).url_for(viewname, *args, **kwargs)


def get_dynamic_static_url(request, static_path):
    """Build a fully-qualified proxy-aware URL for a static file."""
    return ProxyContext.from_request(request).static_url(static_path)
