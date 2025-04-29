# backend/routing.py
from django.urls import re_path
# Import consumers from the *same* app ('backend' in this case)
from . import consumers

websocket_urlpatterns = [
    # Maps the URL '/ws/tracker/' to the BallTrackerConsumer
    re_path(r'ws/tracker/$', consumers.BallTrackerConsumer.as_asgi()),
    # Add other WebSocket paths here if needed
]