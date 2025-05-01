# backend/serializers.py # Assuming this is the correct path
from rest_framework import serializers
from .models import (
    Point,
    Coordinate,
)  # Use '.' if models.py is in the same app directory


class CoordinateSerializer(serializers.ModelSerializer):
    """
    Serializer for individual Coordinate data points needed for replay.
    """

    class Meta:
        model = Coordinate
        fields = ["relative_time_ms", "x", "y", "z"]


class PointSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Points, showing summary information and start context.
    Used for the list where users select a point to replay.
    """

    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = Point
        fields = [
            "id",
            "recorded_start_time",
            "recorded_end_time",  # Good to know when it ended
            "duration_seconds",
            # --- Context at START of point ---
            "server_player",
            "set_number_at_start",
            "team1_games_at_start",
            "team1_points_at_start",
            "team2_games_at_start",
            "team2_points_at_start",
            # --- Context at END of point (Optional for list view) ---
            # 'set_number_at_end',
            # 'team1_games_at_end',
            # 'team1_points_at_end',
            # 'team2_games_at_end',
            # 'team2_points_at_end',
        ]


class PointReplaySerializer(serializers.ModelSerializer):
    """
    Serializer specifically for fetching all data needed to replay a single Point,
    including starting context for the scoreboard during replay.
    """

    coordinates = CoordinateSerializer(many=True, read_only=True)
    # Optionally include duration if the replay UI wants to show it
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = Point
        fields = [
            "id",
            "recorded_start_time",
            "duration_seconds",  # Added duration here too
            # --- Context at START of point (Needed for replay scoreboard) ---
            "server_player",
            "set_number_at_start",
            "team1_games_at_start",
            "team1_points_at_start",
            "team2_games_at_start",
            "team2_points_at_start",
            # --- Coordinates for the replay animation ---
            "coordinates",
        ]  # tracker/serializers.py


from rest_framework import serializers
from .models import Point, Coordinate


class CoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ["relative_time_ms", "x", "y", "z"]  # Only fields needed for replay


class PointSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.ReadOnlyField()  # Use the model property

    class Meta:
        model = Point
        fields = [
            "id",
            "recorded_start_time",
            "recorded_end_time",
            "duration_seconds",
            # Add context fields if you stored them
            # 'server_player',
            # 'team1_score_at_start',
            # 'team2_score_at_start',
        ]


class PointReplaySerializer(serializers.ModelSerializer):
    coordinates = CoordinateSerializer(many=True, read_only=True)

    class Meta:
        model = Point
        fields = ["id", "recorded_start_time", "coordinates"]
