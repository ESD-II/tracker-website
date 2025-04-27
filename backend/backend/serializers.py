# tracker/serializers.py
from rest_framework import serializers
from .models import Point, Coordinate

class CoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ['relative_time_ms', 'x', 'y', 'z'] # Only fields needed for replay

class PointSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.ReadOnlyField() # Use the model property

    class Meta:
        model = Point
        fields = [
            'id',
            'recorded_start_time',
            'recorded_end_time',
            'duration_seconds',
            # Add context fields if you stored them
            # 'server_player',
            # 'team1_score_at_start',
            # 'team2_score_at_start',
        ]

class PointReplaySerializer(serializers.ModelSerializer):
    coordinates = CoordinateSerializer(many=True, read_only=True)

    class Meta:
        model = Point
        fields = ['id', 'recorded_start_time', 'coordinates']