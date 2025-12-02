"""WSGI config for MAST_gui project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MAST_gui.settings')
application = get_wsgi_application()
