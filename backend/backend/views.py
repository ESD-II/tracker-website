# tracker/views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Point
from .serializers import PointSerializer, PointReplaySerializer

class PointListView(generics.ListAPIView):
    """
    Lists all recorded points available for replay.
    Ordered by most recent first.
    """
    queryset = Point.objects.filter(recorded_end_time__isnull=False).order_by('-recorded_start_time') # Only completed points
    serializer_class = PointSerializer

class PointReplayView(generics.RetrieveAPIView):
    """
    Retrieves a specific point along with all its coordinates for replay.
    Coordinates are ordered by relative_time_ms.
    """
    queryset = Point.objects.all()
    serializer_class = PointReplaySerializer
    lookup_field = 'pk' # 'pk' is the default, can be 'id'