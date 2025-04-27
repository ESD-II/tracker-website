# tracker/management/commands/run_mqtt_bridge.py
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone # For timezone-aware datetimes
from tracker.models import Point, Coordinate # Import your models
import json 
import time # For monotonic clock for relative timing
import os

MQTT_BROKER = os.environ.get("MQTT_BROKER", "benjaminf.net")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1884))
MQTT_TOPIC_COORDS = "tennis/scoreboard/ball_coords"
MQTT_TOPIC_OUT = "tennis/scoreboard/ball_crossed_line"
MQTT_TOPIC_START_CLOCK = "tennis/scoreboard/start_clock"
MQTT_TOPIC_STOP_CLOCK = "tennis/scoreboard/stop_clock"
# Add other scoreboard topics if you want to capture context
MQTT_TOPIC_T1_POINTS = "tennis/scoreboard/team1_points"
MQTT_TOPIC_T2_POINTS = "tennis/scoreboard/team2_points"
# ... etc. for games, server

CHANNEL_GROUP_NAME = 'tennis_updates'

# --- State within the bridge ---
current_point_object = None
point_start_monotonic_time = None # Using time.monotonic() for accurate relative timing
# Optional: store current score to save with Point
current_t1_score = "0"
current_t2_score = "0"
# ...

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Bridge Connected to Broker")
        subscriptions = [
            (MQTT_TOPIC_COORDS, 0),
            (MQTT_TOPIC_OUT, 0),
            (MQTT_TOPIC_START_CLOCK, 0),
            (MQTT_TOPIC_STOP_CLOCK, 0),
            (MQTT_TOPIC_T1_POINTS, 0), # Subscribe to score for context
            (MQTT_TOPIC_T2_POINTS, 0),
            # Add other subscriptions if needed
        ]
        client.subscribe(subscriptions)
        print(f"Subscribed to topics.")
    else:
        print(f"MQTT Connection failed, return code={rc}")

def on_message(client, userdata, msg):
    global current_point_object, point_start_monotonic_time
    global current_t1_score, current_t2_score # Example for context

    print(f"MQTT Message: Topic: {msg.topic}, Payload: {msg.payload.decode()[:60]}...") # Log snippet
    channel_layer = get_channel_layer()
    payload_data = {}
    message_type_for_channels = "unknown" # Type for WebSocket message
    save_to_db = True

    try:
        payload_str = msg.payload.decode("utf-8")

        if msg.topic == MQTT_TOPIC_START_CLOCK:
            message_type_for_channels = "clock_start"
            # --- Start of a new point ---
            if current_point_object:
                print("Warning: Received START_CLOCK while a point was already active. Finalizing previous point.")
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()

            # Create a new Point record
            # Capture current scores if available
            current_point_object = Point.objects.create(
                # Example: store scores at point start
                # team1_score_at_start=current_t1_score,
                # team2_score_at_start=current_t2_score,
            )
            point_start_monotonic_time = time.monotonic() # Record high-precision start time
            print(f"--- DB: New Point created (ID: {current_point_object.id}) ---")
            payload_data = {"signal": "start_clock"}
            save_to_db = False # This message itself isn't a coordinate

        elif msg.topic == MQTT_TOPIC_COORDS:
            message_type_for_channels = "coords"
            coords_list = [float(x.strip()) for x in payload_str.split(',')]
            if len(coords_list) == 3:
                payload_data = {"x": coords_list[0], "y": coords_list[1], "z": coords_list[2]}
                # --- Store coordinate if a point is active ---
                if current_point_object and point_start_monotonic_time is not None:
                    relative_ms = int((time.monotonic() - point_start_monotonic_time) * 1000)
                    Coordinate.objects.create(
                        point=current_point_object,
                        relative_time_ms=relative_ms,
                        x=coords_list[0],
                        y=coords_list[1],
                        z=coords_list[2]
                    )
                    # print(f"DB: Stored coord for Point {current_point_object.id} at {relative_ms}ms")
                else:
                    print("Warning: Received coords but no active point. Ignoring DB store for this coord.")
                    save_to_db = False # Don't save if no active point
            else:
                print(f"Warning: Invalid coordinate format: {payload_str}")
                save_to_db = False

        elif msg.topic == MQTT_TOPIC_OUT or msg.topic == MQTT_TOPIC_STOP_CLOCK:
            if msg.topic == MQTT_TOPIC_OUT:
                message_type_for_channels = "out_signal"
                payload_data = {"signal": "out"}
            else: # STOP_CLOCK
                message_type_for_channels = "clock_stop"
                payload_data = {"signal": "stop_clock"}

            # --- End of the current point ---
            if current_point_object:
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()
                print(f"--- DB: Point {current_point_object.id} ended and saved. Duration: {current_point_object.duration_seconds or 'N/A'}s ---")
                current_point_object = None # Reset for the next point
                point_start_monotonic_time = None
            else:
                print("Warning: Received OUT/STOP_CLOCK but no active point.")
            save_to_db = False # These messages finalize, not add coords

        # --- Handle Scoreboard Updates (Optional Context) ---
        elif msg.topic == MQTT_TOPIC_T1_POINTS:
            current_t1_score = payload_str
            message_type_for_channels = "score_update"
            payload_data = {"team": 1, "type": "points", "value": payload_str}
            save_to_db = False # Just update context, not a direct coordinate
        # ... handle other scoreboard topics similarly ...

        else:
            print(f"Warning: Unhandled topic: {msg.topic}")
            save_to_db = False # Don't save unhandled topics by default
            return # Don't forward unhandled to channels either unless desired

        # Send data to the channel layer group (for live view)
        if message_type_for_channels != "unknown":
            async_to_sync(channel_layer.group_send)(
                CHANNEL_GROUP_NAME,
                {
                    'type': 'tracker.update',
                    'data': {
                        'type': message_type_for_channels,
                        'payload': payload_data
                    }
                }
            )

    except Exception as e:
        print(f"Error processing MQTT message or interacting with DB/Channels: {e}")
        print(f"Topic: {msg.topic}, Payload: {msg.payload}")


class Command(BaseCommand):
    help = 'Runs MQTT client bridge, forwards to Channels, and stores data to DB'

    def handle(self, *args, **options):
        # Ensure Django is fully initialized for DB access
        # This is implicitly handled by BaseCommand
        print("Initializing MQTT Bridge with DB support...")

        client = mqtt.Client(client_id="django_db_bridge_" + str(int(time.time())))
        client.on_connect = on_connect
        client.on_message = on_message

        print(f"Attempting to connect to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            self.stderr.write(f"Error connecting to MQTT Broker: {e}")
            return

        self.stdout.write(self.style.SUCCESS('MQTT Bridge started. Listening for messages...'))
        try:
             client.loop_forever()
        except KeyboardInterrupt:
             self.stdout.write(self.style.WARNING('MQTT Bridge stopping...'))
             # Finalize any active point on exit
             global current_point_object
             if current_point_object:
                 print("Finalizing active point on shutdown...")
                 current_point_object.recorded_end_time = timezone.now()
                 current_point_object.save()
                 print(f"Point {current_point_object.id} finalized.")
             client.disconnect()
             self.stdout.write(self.style.SUCCESS('MQTT Bridge stopped.'))