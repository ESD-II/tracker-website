"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
# --- ADD THIS SECTION ---
from dotenv import load_dotenv
# --- END OF ADDED SECTION ---

from channels.routing import ProtocolTypeRouter, URLRouter # Example if using Channels
from django.core.asgi import get_asgi_application
# Import your routing if using Channels
# import backend.routing

# --- ADD THIS LINE ---
load_dotenv() # Load .env before accessing settings
# --- END OF ADDED LINE ---

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') # Adjust if needed

# Example Channels Setup (adjust if not using Channels or if routing is elsewhere)
django_asgi_app = get_asgi_application()
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": URLRouter(
    #     backend.routing.websocket_urlpatterns # Adjust path to your routing
    # ),
})