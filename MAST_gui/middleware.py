from django.conf import settings
from django.shortcuts import resolve_url
from django.http import HttpResponseRedirect
from urllib.parse import urlparse, urlunparse, urlencode

try:
    from views.urls import get_dynamic_url
except ImportError:
    get_dynamic_url = None  # Fallback if not available

class ProxyAwareLoginRedirectMiddleware:
    """
    Middleware to rewrite login redirects to be proxy-aware using proxy headers.
    Place this after AuthenticationMiddleware in MIDDLEWARE.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Only rewrite for GET/HEAD requests
        if request.method not in ("GET", "HEAD"):
            return response
        # Only rewrite 302/301 redirects to LOGIN_URL
        if response.status_code in (301, 302):
            location = response.get('Location', '')
            login_url = resolve_url(getattr(settings, 'LOGIN_URL', '/admin/login/'))
            # Prevent infinite loop: if already on login page, don't rewrite
            if request.path == login_url or request.path.startswith(login_url):
                return response
            # If the redirect is to the login URL (without domain)
            if location and login_url and location.startswith(login_url):
                if get_dynamic_url:
                    # Build proxy-aware login URL
                    # Preserve next param if present
                    parsed = urlparse(location)
                    query = dict()
                    if parsed.query:
                        from urllib.parse import parse_qs
                        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                    next_param = query.get('next')
                    proxy_login_url = get_dynamic_url(request, 'login')
                    if next_param:
                        proxy_login_url += '?' + urlencode({'next': next_param})
                    return HttpResponseRedirect(proxy_login_url)
        return response
