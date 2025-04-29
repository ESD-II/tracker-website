# backend/management/commands/run_mqtt_bridge.py
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
# Make sure the import path is correct for your models
from backend.models import Point, Coordinate
import json
import time
import os

# --- MQTT Configuration ---
MQTT_BROKER = os.environ.get("MQTT_BROKER", "tracker_mqtt") # Default to service name
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))       # Default to internal port

# --- Topic Definitions ---
# Using a dictionary for easier management
MQTT_TOPICS = {
    "coords": "tennis/scoreboard/ball_coords",
    "out": "tennis/scoreboard/ball_crossed_line",
    "start_clock": "tennis/scoreboard/start_clock",
    "stop_clock": "tennis/scoreboard/stop_clock",
    "reset_clock": "tennis/scoreboard/reset_clock", # Added reset
    "t1_points": "tennis/scoreboard/team1_points",
    "t2_points": "tennis/scoreboard/team2_points",
    "t1_games": "tennis/scoreboard/team1_games",
    "t2_games": "tennis/scoreboard/team2_games",
    "clock": "tennis/scoreboard/clock" # Added clock topic
}

CHANNEL_GROUP_NAME = 'tennis_updates'

# --- Global State Variables ---
# Store the *latest known* state of the scoreboard
current_point_object = None
point_start_monotonic_time = None
current_t1_points = "0"
current_t2_points = "0"
current_t1_games = 0
current_t2_games = 0
current_set_number = 1
# Could add current_server if needed/available via MQTT

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print(f"MQTT Bridge Connected to Broker: {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to all defined topics
        subscriptions = [(topic, 0) for topic in MQTT_TOPICS.values()]
        client.subscribe(subscriptions)
        print(f"Subscribed to {len(subscriptions)} topics.")
    else:
        print(f"MQTT Connection failed, return code={rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    # Make sure we can modify the global state variables
    global current_point_object, point_start_monotonic_time
    global current_t1_points, current_t2_points
    global current_t1_games, current_t2_games, current_set_number

    print(f"MQTT Message Received - Topic: {msg.topic}, Payload: '{msg.payload.decode()[:60]}...'")
    channel_layer = get_channel_layer()
    if not channel_layer:
        print("Error: Could not get channel layer. Check Redis connection and Channels setup.")
        return

    payload_data = {}
    message_type_for_channels = "unknown" # Type for WebSocket message

    try:
        payload_str = msg.payload.decode("utf-8")
        topic = msg.topic # For easier comparison

        # --- Handle Point Start/End and Clock Signals ---
        if topic == MQTT_TOPICS["start_clock"]:
            message_type_for_channels = "clock_start"
            if current_point_object:
                print(f"Warning: START_CLOCK received while Point {current_point_object.id} was active. Finalizing previous.")
                # Populate _at_end fields before saving the dangling point
                current_point_object.team1_points_at_end = current_t1_points
                current_point_object.team2_points_at_end = current_t2_points
                current_point_object.team1_games_at_end = current_t1_games
                current_point_object.team2_games_at_end = current_t2_games
                current_point_object.set_number_at_end = current_set_number
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()

            # Create a new Point record, capturing current state at start
            current_point_object = Point.objects.create(
                # server_player = ?, # Add if available
                team1_points_at_start=current_t1_points,
                team2_points_at_start=current_t2_points,
                team1_games_at_start=current_t1_games,
                team2_games_at_start=current_t2_games,
                set_number_at_start=current_set_number
            )
            point_start_monotonic_time = time.monotonic()
            print(f"--- DB: New Point created (ID: {current_point_object.id}) with start state ({current_t1_points}-{current_t2_points} / {current_t1_games}-{current_t2_games} Set {current_set_number}) ---")
            payload_data = {"signal": "start"} # Payload for frontend

        elif topic == MQTT_TOPICS["stop_clock"] or topic == MQTT_TOPICS["out"]:
            message_type_for_channels = "clock_stop" if topic == MQTT_TOPICS["stop_clock"] else "out_signal"
            payload_data = {"signal": "stop"} if topic == MQTT_TOPICS["stop_clock"] else {"signal": "out"}

            if current_point_object:
                # Populate _at_end fields with the *current* state before saving
                current_point_object.team1_points_at_end = current_t1_points
                current_point_object.team2_points_at_end = current_t2_points
                current_point_object.team1_games_at_end = current_t1_games
                current_point_object.team2_games_at_end = current_t2_games
                current_point_object.set_number_at_end = current_set_number
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()
                duration = current_point_object.duration_seconds
                print(f"--- DB: Point {current_point_object.id} ended and saved. Duration: {duration if duration is not None else 'N/A':.2f}s ---")
                current_point_object = None # Reset for the next point
                point_start_monotonic_time = None
            else:
                print("Warning: Received STOP_CLOCK/OUT but no active point.")

        elif topic == MQTT_TOPICS["reset_clock"]:
             message_type_for_channels = "clock_reset"
             payload_data = {"signal": "reset"}
             # Does not affect DB point records directly

        # --- Handle Coordinate Updates ---
        elif topic == MQTT_TOPICS["coords"]:
            message_type_for_channels = "coords"
            try:
                coords_list = [float(x.strip()) for x in payload_str.split(',')]
                if len(coords_list) == 3:
                    payload_data = {"x": coords_list[0], "y": coords_list[1], "z": coords_list[2]}
                    if current_point_object and point_start_monotonic_time is not None:
                        relative_ms = int((time.monotonic() - point_start_monotonic_time) * 1000)
                        # Optimization: Consider batching Coordinate creates if performance is an issue
                        Coordinate.objects.create(
                            point=current_point_object,
                            relative_time_ms=relative_ms,
                            x=coords_list[0],
                            y=coords_list[1],
                            z=coords_list[2]
                        )
                    else:
                        # Don't spam this warning if simulator sends coords between points
                        # print("Debug: Received coords but no active point.")
                        pass # Ignore coords if no point is active
                else:
                    print(f"Warning: Invalid coordinate format: {payload_str}")
            except ValueError:
                 print(f"Warning: Could not parse coordinate values: {payload_str}")

        # --- Handle Scoreboard State Updates ---
        elif topic == MQTT_TOPICS["t1_points"]:
            current_t1_points = payload_str # Update state
            message_type_for_channels = "score_update"
            payload_data = {"team": 1, "type": "points", "value": payload_str}

        elif topic == MQTT_TOPICS["t2_points"]:
            current_t2_points = payload_str # Update state
            message_type_for_channels = "score_update"
            payload_data = {"team": 2, "type": "points", "value": payload_str}

        elif topic == MQTT_TOPICS["t1_games"]:
             message_type_for_channels = "score_update"
             try:
                 parts = payload_str.split(',')
                 if len(parts) == 2:
                     current_t1_games = int(parts[0].strip())
                     current_set_number = int(parts[1].strip()) # Assume set number is same for both
                     print(f"State Update: T1 Games={current_t1_games}, Set={current_set_number}")
                     payload_data = {"team": 1, "type": "games", "games": current_t1_games, "set": current_set_number}
                 else:
                     print(f"Warning: Invalid team1_games format: {payload_str}")
             except ValueError:
                 print(f"Warning: Could not parse team1_games data: {payload_str}")

        elif topic == MQTT_TOPICS["t2_games"]:
             message_type_for_channels = "score_update"
             try:
                 parts = payload_str.split(',')
                 if len(parts) == 2:
                     current_t2_games = int(parts[0].strip())
                     # Don't necessarily overwrite set number if T1 already set it
                     set_num_t2 = int(parts[1].strip())
                     if set_num_t2 != current_set_number:
                          print(f"Warning: Set number mismatch between T1 ({current_set_number}) and T2 ({set_num_t2}). Using T2's value.")
                          current_set_number = set_num_t2
                     print(f"State Update: T2 Games={current_t2_games}, Set={current_set_number}")
                     payload_data = {"team": 2, "type": "games", "games": current_t2_games, "set": current_set_number}
                 else:
                     print(f"Warning: Invalid team2_games format: {payload_str}")
             except ValueError:
                 print(f"Warning: Could not parse team2_games data: {payload_str}")

        elif topic == MQTT_TOPICS["clock"]:
            # Just forward the clock value, don't store state in DB usually
             message_type_for_channels = "clock_update"
             payload_data = {"time": payload_str}

        else:
            print(f"Warning: Received message on unhandled topic: {topic}")
            # Important: Don't send unknown message types to channel layer
            message_type_for_channels = "unknown"

        # --- Send to Channels if relevant ---
        if message_type_for_channels != "unknown":
            # Prepare the message structure expected by the consumer
            channel_message = {
                'type': 'tracker_update', # Must match consumer method name
                'data': {
                    'type': message_type_for_channels,
                    'payload': payload_data
                }
            }
            # Send asynchronously to the group
            async_to_sync(channel_layer.group_send)(
                CHANNEL_GROUP_NAME,
                channel_message
            )
            # print(f"Sent to Channels Group '{CHANNEL_GROUP_NAME}': {channel_message}") # Optional Debug

    except UnicodeDecodeError:
        print(f"Error: Could not decode payload for topic {msg.topic}. Payload: {msg.payload}")
    except Exception as e:
        print(f"Error processing MQTT message or interacting with DB/Channels: {e}")
        print(f"Topic: {msg.topic}, Raw Payload: {msg.payload}")


class Command(BaseCommand):
    help = 'Runs MQTT client bridge, forwards to Channels, and stores scoreboard context to DB'

    def handle(self, *args, **options):
        print("Initializing MQTT Bridge with DB support...")

        # Initialize MQTT Client
        client = mqtt.Client(client_id=f"django_bridge_{os.getpid()}_{int(time.time())}")
        # Assign callbacks
        client.on_connect = on_connect
        client.on_message = on_message
        # Optional: Add on_disconnect, on_log callbacks for more debugging

        print(f"Attempting to connect to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        try:
            # Connect to the broker
            # Keepalive defaults to 60 seconds
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except ConnectionRefusedError:
             self.stderr.write(f"Error: Connection to MQTT Broker {MQTT_BROKER}:{MQTT_PORT} refused. Is it running and accessible?")
             return
        except OSError as e: # Catch broader network errors like 'Network is unreachable'
             self.stderr.write(f"Error connecting to MQTT Broker {MQTT_BROKER}:{MQTT_PORT}: {e}")
             return
        except Exception as e: # Catch other potential errors during connect
            self.stderr.write(f"Unexpected error connecting to MQTT Broker: {e}")
            return

        self.stdout.write(self.style.SUCCESS('MQTT Bridge connection initiated. Starting loop...'))

        # Start the MQTT network loop
        # loop_forever() blocks execution, handles reconnects automatically.
        try:
             client.loop_forever()
        except KeyboardInterrupt:
             self.stdout.write(self.style.WARNING('\nMQTT Bridge stopping due to KeyboardInterrupt...'))
        except Exception as e:
             self.stderr.write(f"An error occurred in the MQTT loop: {e}")
        finally:
             # Finalize any active point on exit cleanly
             global current_point_object
             if current_point_object:
                 print("Finalizing active point on shutdown...")
                 # Update end fields before saving
                 current_point_object.team1_points_at_end = current_t1_points
                 current_point_object.team2_points_at_end = current_t2_points
                 current_point_object.team1_games_at_end = current_t1_games
                 current_point_object.team2_games_at_end = current_t2_games
                 current_point_object.set_number_at_end = current_set_number
                 current_point_object.recorded_end_time = timezone.now()
                 current_point_object.save()
                 print(f"Point {current_point_object.id} finalized.")

             print("Disconnecting MQTT client...")
             client.disconnect() # Disconnect gracefully
             client.loop_stop() # Ensure loop thread stops if using loop_start() elsewhere
             self.stdout.write(self.style.SUCCESS('MQTT Bridge stopped.'))