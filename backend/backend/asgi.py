# backend/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack # Import if using auth
from django.core.asgi import get_asgi_application
# --- IMPORT FROM 'backend' ---
import backend.routing # Import this app's routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

django_asgi_app = get_asgi_application()

print("ASGI Application Instantiated - Daphne is ready to route.")

application = ProtocolTypeRouter({
  "http": django_asgi_app,
  "websocket": AuthMiddlewareStack( # Usually wrap in AuthMiddlewareStack
      URLRouter(
          # --- USE 'backend' ROUTING HERE ---
          backend.routing.websocket_urlpatterns
      )
  ),
})