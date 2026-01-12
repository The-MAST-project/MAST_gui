from django.conf import settings
from django.urls import reverse

def get_dynamic_static_url(request, static_path):
    """
    Generate a fully qualified static file URL using proxy headers if present.
    static_path: relative path to the static file (e.g., 'css/style.css')
    """
    # Ensure leading slash for static path
    if not static_path.startswith('/'):
        static_path = '/' + static_path
    static_url = getattr(settings, 'STATIC_URL', '/static/')
    if static_url.endswith('/'):
        static_url = static_url[:-1]
    path = f"{static_url}{static_path}"
    headers = request.META
    proxy_base = headers.get('HTTP_X_PROXY_BASE', '')
    proxy_port = headers.get('HTTP_X_PROXY_PORT')
    external_ip = headers.get('HTTP_X_PROXY_EXTERNAL_IP')
    scheme = request.scheme

    if external_ip:
        port = f":{proxy_port}" if proxy_port else ''
        base = proxy_base.rstrip('/')
        url = f"{scheme}://{external_ip}{port}{base}{path}"
    else:
        url = request.build_absolute_uri(path)
    return url


def get_dynamic_url(request, viewname, *args, **kwargs):
    """
    Generate a fully qualified URL using proxy headers if present.
    Looks for x-proxy-base, x-proxy-port, and x-external-ip in the request headers.
    Falls back to request.get_host() and request.scheme if not present.
    """
    path = reverse(viewname, args=args, kwargs=kwargs)
    headers = request.META
    proxy_base = headers.get('HTTP_X_PROXY_BASE', '')
    proxy_port = headers.get('HTTP_X_PROXY_PORT')
    external_ip = headers.get('HTTP_X_PROXY_EXTERNAL_IP')
    scheme = request.scheme

    if external_ip:
        # Use proxy headers to build the external URL
        port = f":{proxy_port}" if proxy_port else ''
        base = proxy_base.rstrip('/')
        # url = f"{scheme}://{external_ip}{port}{base}{path}"
        url = f"{scheme}://{external_ip}{port}{path}"
    else:
        # Fallback to the default host
        url = request.build_absolute_uri(path)
    return url
