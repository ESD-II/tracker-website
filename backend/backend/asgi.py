# backend/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
# Import your routing and potentially middleware if needed later
import backend.routing # Assuming your websocket routing is here

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup() # Setup django early if needed by middleware below

# Get the standard Django ASGI app first
django_asgi_app = get_asgi_application()

# --- ADD LOGGING ---
print("ASGI Application Instantiated - Daphne is ready to route.")
# --- END LOGGING ---

application = ProtocolTypeRouter({
    "http": django_asgi_app, # Use the standard Django ASGI app for HTTP
    "websocket": URLRouter( # Only use URLRouter for websockets
            backend.routing.websocket_urlpatterns
        )
    # Add AuthMiddlewareStack here if needed for websockets:
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(
    #         backend.routing.websocket_urlpatterns
    #     )
    # ),
})

# --- ADD MORE LOGGING ---
# You could potentially wrap the application callable to log each incoming scope
# (More advanced, try simpler steps first)
# original_application = application
# async def logging_application_wrapper(scope, receive, send):
#     print(f"ASGI Scope Received: {scope.get('type', 'unknown')} {scope.get('path', '')}")
#     await original_application(scope, receive, send)
# application = logging_application_wrapper
# --- END MORE LOGGING ---