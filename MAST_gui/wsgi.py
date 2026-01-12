"""WSGI config for MAST_gui project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MAST_gui.settings')

def detect_script_name(environ):
    # Detect SCRIPT_NAME from common proxy headers
    # X-Forwarded-Prefix is set by many reverse proxies (nginx, traefik, etc.)
    xf_prefix = environ.get('HTTP_X_PROXY_BASE')
    if xf_prefix:
        # Ensure leading slash, remove trailing slash
        prefix = xf_prefix
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        return prefix.rstrip('/')
    # Try standard SCRIPT_NAME if set by the proxy
    script_name = environ.get('SCRIPT_NAME')
    if script_name:
        return script_name.rstrip('/')
    # Fallback to environment variable
    env_script_name = os.environ.get("MAST_SCRIPT_NAME", "")
    if env_script_name:
        if not env_script_name.startswith('/'):
            env_script_name = '/' + env_script_name
        return env_script_name.rstrip('/')
    return ''

from django.core.handlers.wsgi import WSGIHandler

class ScriptNameDetectingWSGIHandler(WSGIHandler):
    def __call__(self, environ, start_response):
        script_name = detect_script_name(environ)
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            # Also set FORCE_SCRIPT_NAME for Django's URL resolver
            os.environ['FORCE_SCRIPT_NAME'] = script_name
        return super().__call__(environ, start_response)

application = ScriptNameDetectingWSGIHandler()
