# tracker/models.py
from django.db import models
from django.utils import timezone

class Point(models.Model):
    """Represents a single point played, from serve to end."""
    # Timestamps from the perspective of when the server recorded it
    recorded_start_time = models.DateTimeField(auto_now_add=True, db_index=True)
    recorded_end_time = models.DateTimeField(null=True, blank=True)

    # Optional: Data from scoreboard at the start of the point
    server_player = models.IntegerField(null=True, blank=True) # e.g., 1 or 2
    team1_score_at_start = models.CharField(max_length=10, null=True, blank=True)
    team2_score_at_start = models.CharField(max_length=10, null=True, blank=True)
    # ... any other context you want to save

    def __str__(self):
        return f"Point {self.id} started at {self.recorded_start_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def duration_seconds(self):
        if self.recorded_start_time and self.recorded_end_time:
            return (self.recorded_end_time - self.recorded_start_time).total_seconds()
        return None

class Coordinate(models.Model):
    """Stores a single coordinate (x, y, z) for a ball within a point."""
    point = models.ForeignKey(Point, related_name='coordinates', on_delete=models.CASCADE)
    # Timestamp relative to the start of *this specific point's simulation/recording*
    # This is crucial for accurate replay timing.
    relative_time_ms = models.PositiveIntegerField(help_text="Milliseconds since point start")
    timestamp_abs = models.DateTimeField(auto_now_add=True, help_text="Absolute time coord was saved")

    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()

    class Meta:
        ordering = ['relative_time_ms'] # Essential for replaying in order

    def __str__(self):
        return f"Coord ({self.x:.2f}, {self.y:.2f}, {self.z:.2f}) at {self.relative_time_ms}ms for Point {self.point_id}"