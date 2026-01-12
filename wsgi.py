import os
import sys

from django.core.wsgi import get_wsgi_application
from django.urls import set_script_prefix

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def _get_wsgi_application():
    return get_wsgi_application()

def application(environ, start_response):
    proxy_base = environ.get('HTTP_X_PROXY_BASE')
    if proxy_base:
        set_script_prefix(proxy_base.rstrip('/'))
    else:
        set_script_prefix('')
    return _get_wsgi_application()(environ, start_response)

if 'runserver' in sys.argv or 'test' in sys.argv:
    application = _get_wsgi_application()

debug = os.environ.get('DJANGO_DEBUG', '').lower() in ('true', '1', 't')
if debug:
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8010'])
