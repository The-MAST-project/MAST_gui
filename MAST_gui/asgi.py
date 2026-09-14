"""ASGI config for MAST_gui project."""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAST_gui.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        # WebSocket routing will be added here
    }
)
