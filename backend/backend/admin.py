# backend/admin.py
from django.contrib import admin
from .models import Point, Coordinate


class PointAdmin(admin.ModelAdmin):
    list_display = ("id", "recorded_start_time", "recorded_end_time")
    # Add other fields you want to display for Point


class CoordinateAdmin(admin.ModelAdmin):
    list_display = ("id", "point", "relative_time_ms", "x", "y", "z")
    # search_fields = ("point__id", "relative_time_ms")


admin.site.register(Point, PointAdmin)
admin.site.register(Coordinate, CoordinateAdmin)
