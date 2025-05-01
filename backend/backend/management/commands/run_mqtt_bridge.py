# backend/management/commands/run_mqtt_bridge.py
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
# --- Removed Channels/Async imports ---
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from django.utils import timezone
# Ensure this matches your project structure where models.py lives
from backend.models import Point, Coordinate
import json
import time
import os

# --- MQTT Configuration ---
# Read from environment or use defaults suitable for Docker internal network
MQTT_BROKER = os.environ.get("MQTT_BROKER", "tracker_mqtt")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))

# --- Topic Definitions ---
# Using a dictionary for easier management and subscription
MQTT_TOPICS = {
    "coords":      "tennis/scoreboard/ball_coords",
    "out":         "tennis/scoreboard/ball_crossed_line",
    "start_clock": "tennis/scoreboard/start_clock",
    "stop_clock":  "tennis/scoreboard/stop_clock",
    "reset_clock": "tennis/scoreboard/reset_clock", # Topic exists, but no action needed for DB
    "t1_points":   "tennis/scoreboard/team1_points",
    "t2_points":   "tennis/scoreboard/team2_points",
    "t1_games":    "tennis/scoreboard/team1_games",
    "t2_games":    "tennis/scoreboard/team2_games",
    "clock":       "tennis/scoreboard/clock",      # Topic exists, but no action needed for DB
    # Add any other topics your simulator might send (e.g., server changes)
    # "server":      "tennis/scoreboard/server"
}

# --- REMOVED CHANNEL_GROUP_NAME ---

# --- Global State Variables ---
# Store the *latest known* state received from MQTT for context saving
current_point_object = None             # Holds the active Point DB object
point_start_monotonic_time = None       # For calculating relative coord time
current_t1_points = "0"
current_t2_points = "0"
current_t1_games = 0
current_t2_games = 0
current_set_number = 1
current_server_player = None            # Track server if MQTT provides it

# --- MQTT Callbacks ---

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print(f"MQTT Bridge Connected to Broker: {MQTT_BROKER}:{MQTT_PORT}")
        subscriptions = [(topic, 0) for topic in MQTT_TOPICS.values()]
        client.subscribe(subscriptions)
        print(f"Subscribed to {len(subscriptions)} topics.")
    else:
        print(f"MQTT Connection failed, return code={rc}. Check broker status.")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects."""
    print(f"MQTT Bridge Disconnected, return code={rc}. Loop should handle reconnect.")

def on_message(client, userdata, msg):
    """
    Callback for when a message is received from the MQTT broker.
    Updates internal state and saves relevant data directly to the DB.
    """
    global current_point_object, point_start_monotonic_time
    global current_t1_points, current_t2_points, current_t1_games, current_t2_games
    global current_set_number, current_server_player

    print(f"MQTT Message Received - Topic: {msg.topic}, Payload: '{msg.payload.decode()[:60]}...'")

    # --- REMOVED Channel layer logic ---

    try:
        payload_str = msg.payload.decode("utf-8").strip()
        topic = msg.topic

        # --- POINT START/END HANDLING ---
        if topic == MQTT_TOPICS["start_clock"]:
            if current_point_object:
                print(f"Warning: START_CLOCK received while Point {current_point_object.id} was active. Finalizing previous point.")
                # Save end state if needed, similar to stop_clock logic
                current_point_object.team1_points_at_end = current_t1_points
                current_point_object.team2_points_at_end = current_t2_points
                current_point_object.team1_games_at_end = current_t1_games
                current_point_object.team2_games_at_end = current_t2_games
                current_point_object.set_number_at_end = current_set_number
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()

            # Create the new Point record, capturing the state at start
            current_point_object = Point.objects.create(
                team1_points_at_start=current_t1_points,
                team2_points_at_start=current_t2_points,
                team1_games_at_start=current_t1_games,
                team2_games_at_start=current_t2_games,
                set_number_at_start=current_set_number,
                server_player=current_server_player
            )
            point_start_monotonic_time = time.monotonic()
            print(f"--- DB: New Point created (ID: {current_point_object.id}) with start state ({current_t1_points}-{current_t2_points} / {current_t1_games}-{current_t2_games} Set {current_set_number}) ---")

        elif topic == MQTT_TOPICS["stop_clock"] or topic == MQTT_TOPICS["out"]:
            if current_point_object:
                # Finalize the active point using the *current* global state
                current_point_object.team1_points_at_end = current_t1_points
                current_point_object.team2_points_at_end = current_t2_points
                current_point_object.team1_games_at_end = current_t1_games
                current_point_object.team2_games_at_end = current_t2_games
                current_point_object.set_number_at_end = current_set_number
                current_point_object.recorded_end_time = timezone.now()
                current_point_object.save()
                duration = current_point_object.duration_seconds
                print(f"--- DB: Point {current_point_object.id} ended and saved. Duration: {duration if duration is not None else 'N/A':.2f}s ---")

                current_point_object = None
                point_start_monotonic_time = None
            else:
                print("Warning: Received STOP_CLOCK/OUT but no active point.")

        # --- COORDINATE UPDATES ---
        elif topic == MQTT_TOPICS["coords"]:
            try:
                coords_list = [float(x.strip()) for x in payload_str.split(',')]
                if len(coords_list) == 3:
                    # Save to DB only if a point is currently active
                    if current_point_object and point_start_monotonic_time is not None:
                        relative_ms = int((time.monotonic() - point_start_monotonic_time) * 1000)
                        Coordinate.objects.create(
                            point=current_point_object,
                            relative_time_ms=relative_ms,
                            x=coords_list[0],
                            y=coords_list[1],
                            z=coords_list[2]
                        )
                    # No else needed, just ignore coords if no point active
                else:
                    print(f"Warning: Invalid coordinate format received: {payload_str}")
            except ValueError:
                 print(f"Warning: Could not parse coordinate float values: {payload_str}")

        # --- SCOREBOARD STATE UPDATES (Update internal state only) ---
        elif topic == MQTT_TOPICS["t1_points"]:
            current_t1_points = payload_str # Update internal state

        elif topic == MQTT_TOPICS["t2_points"]:
            current_t2_points = payload_str # Update internal state

        elif topic == MQTT_TOPICS["t1_games"]:
             try:
                 parts = payload_str.split(',')
                 if len(parts) == 2:
                     current_t1_games = int(parts[0].strip())
                     current_set_number = int(parts[1].strip())
                     print(f"State Update: T1 Games={current_t1_games}, Set={current_set_number}")
                 else:
                     print(f"Warning: Invalid team1_games format: {payload_str}")
             except ValueError:
                 print(f"Warning: Could not parse team1_games int values: {payload_str}")

        elif topic == MQTT_TOPICS["t2_games"]:
             try:
                 parts = payload_str.split(',')
                 if len(parts) == 2:
                     current_t2_games = int(parts[0].strip())
                     set_num_t2 = int(parts[1].strip())
                     # Optionally check/update set number based on T2 msg
                     if set_num_t2 != current_set_number:
                         print(f"Note: Set number updated based on T2 message ({current_set_number} -> {set_num_t2}).")
                         current_set_number = set_num_t2
                     print(f"State Update: T2 Games={current_t2_games}, Set={current_set_number}")
                 else:
                     print(f"Warning: Invalid team2_games format: {payload_str}")
             except ValueError:
                 print(f"Warning: Could not parse team2_games int values: {payload_str}")

        # --- Topics to Ignore for DB (but keep subscription for state updates) ---
        elif topic == MQTT_TOPICS["clock"] or topic == MQTT_TOPICS["reset_clock"]:
             pass # No database action needed for these

        # --- Handle other topics if added ---
        # elif topic == MQTT_TOPICS["server"]:
        #     try:
        #         current_server_player = int(payload_str)
        #         print(f"State Update: Server = Player {current_server_player}")
        #     except ValueError:
        #          print(f"Warning: Could not parse server player int value: {payload_str}")

        else:
            # Topic wasn't handled by the specific cases above
            print(f"Note: Received message on unhandled topic: {topic}")

        # --- REMOVED channel_layer.group_send logic ---

    except UnicodeDecodeError:
        print(f"Error: Could not decode payload (not UTF-8) for topic {msg.topic}. Payload (raw): {msg.payload}")
    except Exception as e:
        # Catch unexpected errors during processing
        print(f"!!! Unexpected Error processing MQTT message: {e}")
        print(f"    Topic: {msg.topic}, Raw Payload: {msg.payload}")
        import traceback # Optional: Log full traceback for debugging
        print(traceback.format_exc())


# --- Django Management Command ---

class Command(BaseCommand):
    # Updated help text
    help = 'Runs MQTT client bridge: subscribes to topics and stores data directly to DB.'

    def handle(self, *args, **options):
        """Main execution method for the management command."""
        # Updated startup message
        print("Initializing MQTT Bridge (DB Direct Mode)...")

        client_id = f"django_db_bridge_direct_{os.getpid()}_{int(time.time())}"
        client = mqtt.Client(client_id=client_id)

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        print(f"Attempting to connect to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        except ConnectionRefusedError:
             self.stderr.write(self.style.ERROR(f"Error: Connection refused by MQTT Broker {MQTT_BROKER}:{MQTT_PORT}."))
             return
        except OSError as e:
             self.stderr.write(self.style.ERROR(f"Network error connecting to MQTT Broker: {e}"))
             return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error during initial MQTT connection: {e}"))
            return

        self.stdout.write(self.style.SUCCESS('MQTT Bridge connection initiated. Starting loop...'))

        try:
             client.loop_forever()
        except KeyboardInterrupt:
             self.stdout.write(self.style.WARNING('\nMQTT Bridge stopping due to KeyboardInterrupt...'))
        except Exception as e:
             self.stderr.write(self.style.ERROR(f"An critical error occurred in the MQTT loop: {e}"))
        finally:
             # --- Graceful Shutdown ---
             self.stdout.write(self.style.WARNING('Initiating graceful shutdown...'))
             global current_point_object
             if current_point_object:
                 print("Finalizing active point on shutdown...")
                 try:
                     # Populate end fields with the last known state if not already set
                     if not current_point_object.recorded_end_time:
                         current_point_object.team1_points_at_end = current_t1_points
                         current_point_object.team2_points_at_end = current_t2_points
                         current_point_object.team1_games_at_end = current_t1_games
                         current_point_object.team2_games_at_end = current_t2_games
                         current_point_object.set_number_at_end = current_set_number
                         current_point_object.recorded_end_time = timezone.now()
                         current_point_object.save()
                         print(f"Point {current_point_object.id} finalized and saved.")
                     else:
                         print(f"Point {current_point_object.id} was already finalized.")
                 except Exception as save_err:
                     print(f"Error saving final point state on shutdown: {save_err}")

             print("Disconnecting MQTT client...")
             client.disconnect()
             self.stdout.write(self.style.SUCCESS('MQTT Bridge stopped.'))