# backend/models.py  (Assuming your app is named 'backend')
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Point(models.Model):
    """
    Represents a single point played, from serve start to point end.
    Includes scoreboard context captured at the start and end of the point.
    """
    # === Timestamps ===
    # Timestamp from the server's perspective when the point started recording (start_clock received)
    recorded_start_time = models.DateTimeField(auto_now_add=True, db_index=True)
    # Timestamp when the point ended (stop_clock or ball_crossed_line received)
    recorded_end_time = models.DateTimeField(null=True, blank=True, db_index=True)

    # === Context at Point Start ===
    server_player = models.IntegerField(null=True, blank=True, help_text="Player serving (e.g., 1 or 2)")
    team1_points_at_start = models.CharField(max_length=10, null=True, blank=True, help_text="Team 1 points (0, 15, 30, 40, AD) at start")
    team2_points_at_start = models.CharField(max_length=10, null=True, blank=True, help_text="Team 2 points (0, 15, 30, 40, AD) at start")
    team1_games_at_start = models.IntegerField(null=True, blank=True, help_text="Team 1 games won at start of point")
    team2_games_at_start = models.IntegerField(null=True, blank=True, help_text="Team 2 games won at start of point")
    set_number_at_start = models.IntegerField(null=True, blank=True, help_text="Current set number at start of point")

    # === Context at Point End ===
    # Note: These might reflect the score *after* the point outcome is decided
    team1_points_at_end = models.CharField(max_length=10, null=True, blank=True, help_text="Team 1 points (0, 15, 30, 40, AD) at end")
    team2_points_at_end = models.CharField(max_length=10, null=True, blank=True, help_text="Team 2 points (0, 15, 30, 40, AD) at end")
    team1_games_at_end = models.IntegerField(null=True, blank=True, help_text="Team 1 games won at end of point")
    team2_games_at_end = models.IntegerField(null=True, blank=True, help_text="Team 2 games won at end of point")
    set_number_at_end = models.IntegerField(null=True, blank=True, help_text="Current set number at end of point")

    # Optional: Could add a field for point winner if determined by the bridge
    # point_winner = models.IntegerField(null=True, blank=True, help_text="Player who won the point (1 or 2)")

    def __str__(self):
        start_str = self.recorded_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.recorded_start_time else 'No Start Time'
        return f"Point {self.id} started at {start_str}"

    @property
    def duration_seconds(self):
        """Calculates the duration of the point if start and end times are available."""
        if self.recorded_start_time and self.recorded_end_time:
            delta = self.recorded_end_time - self.recorded_start_time
            # Ensure duration is not negative if clocks are slightly off
            return max(0, delta.total_seconds())
        return None

    # Add clean method for potential validation if needed later
    # def clean(self):
    #     if self.recorded_end_time and self.recorded_start_time and self.recorded_end_time < self.recorded_start_time:
    #         raise ValidationError("End time cannot be before start time.")

class Coordinate(models.Model):
    """Stores a single coordinate (x, y, z) for a ball within a point."""
    point = models.ForeignKey(Point, related_name='coordinates', on_delete=models.CASCADE)
    # Timestamp relative to the start of *this specific point's simulation/recording*
    relative_time_ms = models.PositiveIntegerField(db_index=True, help_text="Milliseconds since point start") # Added index
    timestamp_abs = models.DateTimeField(auto_now_add=True, help_text="Absolute time coord was saved")

    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()

    class Meta:
        ordering = ['relative_time_ms'] # Essential for replaying in order

    def __str__(self):
        return f"Coord ({self.x:.2f}, {self.y:.2f}, {self.z:.2f}) at {self.relative_time_ms}ms for Point {self.point_id}"