from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from urllib.parse import parse_qs, urlencode, urlparse

from MAST_common.proxy import ProxyContext

# URL prefixes that unauthenticated users may access freely
_PUBLIC_PREFIXES = (
    '/login/',
    '/logout/',
    '/signup/',
    '/accounts/',   # allauth OAuth callbacks
    '/social/',     # social_force_select
    '/admin/',
    '/api/',
    '/sse/',
    '/controller-status/',
    '/__debug__/',
    '/static/',
    '/media/',
)


class RequireLoginMiddleware:
    """
    Redirects unauthenticated users to the dashboard (welcome page) for any
    full-page GET request that isn't a public URL.
    HTMX partial requests are excluded so they can handle auth errors themselves.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        proxy = ProxyContext.from_request(request)
        dashboard_path = (proxy.base or '') + '/'
        if (
            request.method == 'GET'
            and not request.user.is_authenticated
            and request.path.rstrip('/') + '/' != dashboard_path
            and not request.path.startswith(_PUBLIC_PREFIXES)
            and not any(request.path.startswith((proxy.base or '') + p) for p in _PUBLIC_PREFIXES)
            and not request.headers.get('HX-Request')
        ):
            return HttpResponseRedirect(dashboard_path)
        return self.get_response(request)


class ProxyAwareLoginRedirectMiddleware:
    """
    Rewrites login redirects to include the nginx proxy base path.
    Place after AuthenticationMiddleware in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method not in ("GET", "HEAD"):
            return response
        if response.status_code not in (301, 302):
            return response

        login_url = resolve_url(getattr(settings, "LOGIN_URL", "/login/"))
        location = response.get("Location", "")

        # Avoid infinite redirect loop
        if request.path.startswith(login_url):
            return response
        if not location.startswith(login_url):
            return response

        proxy = ProxyContext.from_request(request)
        if not proxy.proxied:
            return response

        qs = {k: v[0] for k, v in parse_qs(urlparse(location).query).items()}
        new_url = proxy.url_for("login")
        if "next" in qs:
            new_url += "?" + urlencode({"next": qs["next"]})
        return HttpResponseRedirect(new_url)
