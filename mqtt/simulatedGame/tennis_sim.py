#!/usr/bin/env python3

import time
import random
import subprocess
import math
import sys
import os # Import os

# --- Configuration ---
# Use environment variables for MQTT broker/port, fallback to defaults
MQTT_BROKER = os.environ.get("MQTT_BROKER_EXT", "benjaminf.net") # Use external name/IP for simulator
MQTT_PORT = os.environ.get("MQTT_PORT_EXT", "1884")          # Use external port for simulator

SIMULATION_SPEED = 0.2  # Seconds between ball position updates
RALLY_LENGTH_MIN = 5    # Min number of hits in a rally
RALLY_LENGTH_MAX = 10   # Max number of hits in a rally
OUT_PROBABILITY = 0.15  # Probability ball goes out on a given hit (after serve)

# --- Court dimensions (simplified representation) ---
COURT_LENGTH = 23.77
COURT_WIDTH_SINGLES = 8.23
NET_HEIGHT = 0.914
SERVICE_BOX_DEPTH = 6.4

# --- Game State ---
team1_points_str = "0"
team2_points_str = "0"
team1_games = 0
team2_games = 0
current_set = 1
server = 1
serving_side = "deuce"
# *** This variable will now be reset after each game ***
game_time_seconds = 0.0

# --- Point Lookup ---
POINTS_SEQUENCE = ["0", "15", "30", "40", "AD"]

# --- Ball State ---
ball_x = 0.0
ball_y = 0.0
ball_z = 0.0

# --- Helper Functions ---

def publish_mqtt(topic, message):
    """Publishes a message to an MQTT topic using mosquitto_pub."""
    try:
        command = [
            "mosquitto_pub",
            "-h", MQTT_BROKER, # Uses configured broker
            "-p", MQTT_PORT,   # Uses configured port
            "-t", topic,
            "-m", str(message)
        ]
        # print(f"DEBUG MQTT Publish: {' '.join(command)}") # Uncomment for verbose debugging
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=5) # Added timeout
    except FileNotFoundError:
        print("FATAL ERROR: 'mosquitto_pub' command not found.", file=sys.stderr)
        print("Please install mosquitto-clients.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"WARNING: Timeout publishing to MQTT topic '{topic}'. Broker might be slow or down.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Error publishing to MQTT topic '{topic}': {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: An unexpected error occurred during MQTT publish: {e}", file=sys.stderr)

def format_clock(total_seconds):
    """Formats total seconds into MM:SS string."""
    if total_seconds < 0: total_seconds = 0
    minutes = int(total_seconds) // 60
    seconds = int(total_seconds) % 60
    return f"{minutes:02}:{seconds:02}"

def publish_final_clock_time(rally_start_time):
    """Calculates rally duration, updates total time, publishes final clock value."""
    global game_time_seconds
    if rally_start_time is None: return

    rally_duration = time.monotonic() - rally_start_time
    game_time_seconds += rally_duration # Add duration for the point just played

    clock_str = format_clock(game_time_seconds)
    publish_mqtt("tennis/scoreboard/clock", clock_str)
    print(f"Point Duration: {rally_duration:.2f}s. Accumulated Time This Game: {clock_str}") # Clarified log

def get_score_index(score_str):
    """Gets the index of a score string in the sequence."""
    try:
        return POINTS_SEQUENCE.index(score_str)
    except ValueError:
        return -1

def update_score(winner):
    """Updates the points, games, and sets. Resets clock if game ends."""
    # Add game_time_seconds to globals modified by this function
    global team1_points_str, team2_points_str, team1_games, team2_games
    global server, serving_side, current_set, game_time_seconds

    p1_idx = get_score_index(team1_points_str)
    p2_idx = get_score_index(team2_points_str)

    game_over = False
    set_over = False

    # --- Point Logic ---
    if winner == 1:
        if team1_points_str == "40" and team2_points_str in ["0", "15", "30"]: game_over = True
        elif team1_points_str == "40" and team2_points_str == "40": team1_points_str = "AD"
        elif team1_points_str == "40" and team2_points_str == "AD": team2_points_str = "40" # Deuce
        elif team1_points_str == "AD": game_over = True
        else: team1_points_str = POINTS_SEQUENCE[p1_idx + 1]
    else: # winner == 2
        if team2_points_str == "40" and team1_points_str in ["0", "15", "30"]: game_over = True
        elif team2_points_str == "40" and team1_points_str == "40": team2_points_str = "AD"
        elif team2_points_str == "40" and team1_points_str == "AD": team1_points_str = "40" # Deuce
        elif team2_points_str == "AD": game_over = True
        else: team2_points_str = POINTS_SEQUENCE[p2_idx + 1]

    # --- Publish Point Update ---
    publish_mqtt("tennis/scoreboard/team1_points", team1_points_str)
    publish_mqtt("tennis/scoreboard/team2_points", team2_points_str)
    print(f"Score Updated: {team1_points_str}-{team2_points_str}", end='')

    # --- Game/Set Logic ---
    if game_over:
        print(f" -> GAME Player {winner}!")
        team1_points_str = "0" # Reset points for new game
        team2_points_str = "0"
        serving_side = "deuce" # Reset serving side
        if winner == 1: team1_games += 1
        else: team2_games += 1

        # Publish game score immediately after game ends
        publish_mqtt("tennis/scoreboard/team1_games", f"{team1_games},{current_set}")
        publish_mqtt("tennis/scoreboard/team2_games", f"{team2_games},{current_set}")

        # *** RESET CLOCK LOGIC ***
        print(">>> Resetting clock after game.")
        game_time_seconds = 0.0 # Reset the accumulator
        publish_mqtt("tennis/scoreboard/reset_clock", "") # Send reset signal
        publish_mqtt("tennis/scoreboard/clock", format_clock(game_time_seconds)) # Send "00:00"
        # *** END RESET CLOCK LOGIC ***

        # Check for set win
        if (team1_games >= 6 and team1_games >= team2_games + 2) or team1_games == 7:
             set_over = True
             winner_set = 1
        elif (team2_games >= 6 and team2_games >= team1_games + 2) or team2_games == 7:
             set_over = True
             winner_set = 2

        if set_over:
             print(f"*** SET Player {winner_set}! ***")
             # Reset games for next set simulation
             team1_games = 0
             team2_games = 0
             # current_set += 1 # Uncomment to simulate multiple sets
             server = 2 if server == 1 else 1 # Switch server for start of new set
             publish_mqtt("tennis/scoreboard/team1_games", f"{team1_games},{current_set}")
             publish_mqtt("tennis/scoreboard/team2_games", f"{team2_games},{current_set}")
             print(f"Starting Set {current_set} simulation (reset games). Score {team1_games}-{team2_games}. Server: P{server}")
             # Clock already reset by the game ending
        else: # Game over, but set not over
            server = 2 if server == 1 else 1 # Switch server for the next game
            print(f" | Next Game Start. Server: P{server}")

    else: # Point over, but game not over
        # Update serving side
        if team1_points_str == "40" and team2_points_str == "40": serving_side = "deuce"
        elif team1_points_str == "AD" or team2_points_str == "AD": serving_side = "ad"
        else: serving_side = "ad" if serving_side == "deuce" else "deuce"
        print(f" | Server: P{server} ({serving_side})")

    return server, serving_side # Return possibly updated state


# --- Other Functions (get_serve_position, is_out_of_bounds, simulate_rally) ---
# These remain the same as your provided version
def get_serve_position(current_server, current_serving_side):
    x_pos = -COURT_LENGTH / 2 if current_server == 1 else COURT_LENGTH / 2
    y_pos = -COURT_WIDTH_SINGLES * 0.25 if current_serving_side == "deuce" else COURT_WIDTH_SINGLES * 0.25
    z_pos = 1.5
    return x_pos, y_pos, z_pos

def is_out_of_bounds(x, y, z):
    if z < 0:
        if abs(x) > COURT_LENGTH / 2 or abs(y) > COURT_WIDTH_SINGLES / 2:
             return True
        else:
             return False
    return False

def simulate_rally(current_server, current_serving_side):
    global ball_x, ball_y, ball_z
    rally_start_time = time.monotonic()
    publish_mqtt("tennis/scoreboard/start_clock", "")
    point_winner = 0
    ball_x, ball_y, ball_z = get_serve_position(current_server, current_serving_side)
    print(f"\n--- Simulating Point --- Server: P{current_server} ({current_serving_side})")
    publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
    time.sleep(0.5)
    target_x_factor = 0.3
    target_x = (COURT_LENGTH * target_x_factor) if current_server == 1 else (-COURT_LENGTH * target_x_factor)
    target_y = -COURT_WIDTH_SINGLES * 0.25 if current_serving_side == "deuce" else COURT_WIDTH_SINGLES * 0.25
    dx = target_x - ball_x
    dy = target_y - ball_y
    dist_serve = math.sqrt(dx**2 + dy**2) or 1
    steps = 15
    serve_fault = False
    for i in range(1, steps + 1):
        frac = i / steps
        ball_x += dx / steps
        ball_z = 1.5 + math.sin(frac * math.pi) * 1.5
        ball_y += dy / steps
        publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
        time.sleep(SIMULATION_SPEED / 2.5)
        if abs(ball_x) < 0.5 and ball_z < NET_HEIGHT:
             print("Sim Result: Fault (Hit Net)")
             serve_fault = True
             break
    if not serve_fault:
        landed_in_correct_half = (current_server == 1 and ball_x > 0) or (current_server == 2 and ball_x < 0)
        landed_within_sidelines = abs(ball_y) <= COURT_WIDTH_SINGLES / 2
        landed_within_baseline = abs(ball_x) <= COURT_LENGTH / 2
        landed_in_service_area = abs(ball_x) < SERVICE_BOX_DEPTH
        if not (landed_in_correct_half and landed_within_sidelines and landed_within_baseline and landed_in_service_area):
            print("Sim Result: Fault (Serve Out)")
            serve_fault = True
    if serve_fault:
        publish_mqtt("tennis/scoreboard/ball_crossed_line", "1")
        time.sleep(0.5)
        point_winner = 2 if current_server == 1 else 1
        return point_winner, rally_start_time
    ball_z = 0.0
    publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
    time.sleep(0.1)
    current_hitter = 2 if current_server == 1 else 1
    num_hits = random.randint(RALLY_LENGTH_MIN, RALLY_LENGTH_MAX)
    for hit in range(num_hits):
        target_x_side = -COURT_LENGTH / 2 if current_hitter == 2 else COURT_LENGTH / 2
        target_x_rel = random.uniform(0.1, 0.45)
        target_x = target_x_side * (1 - target_x_rel) if target_x_side < 0 else target_x_side * target_x_rel
        target_y = random.uniform(-COURT_WIDTH_SINGLES/2 * 0.95, COURT_WIDTH_SINGLES/2 * 0.95)
        start_x, start_y, start_z = ball_x, ball_y, 0.1
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.sqrt(dx**2 + dy**2) or 1
        steps = max(10, int(dist / 1.5))
        max_arc_height = random.uniform(1.0, 2.5)
        hit_net = False
        for i in range(1, steps + 1):
            frac = i / steps
            prev_x = ball_x
            ball_x = start_x + dx * frac
            ball_y = start_y + dy * frac
            ball_z = start_z + math.sin(frac * math.pi) * max_arc_height
            publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
            time.sleep(SIMULATION_SPEED)
            if (prev_x * ball_x <= 0):
                 if ball_z < NET_HEIGHT:
                     print("Sim Result: Net!")
                     hit_net = True
                     break
        if hit_net:
             publish_mqtt("tennis/scoreboard/ball_crossed_line", "1")
             point_winner = 2 if current_hitter == 1 else 1
             return point_winner, rally_start_time
        if is_out_of_bounds(ball_x, ball_y, -0.01):
             print("Sim Result: Out!")
             publish_mqtt("tennis/scoreboard/ball_crossed_line", "1")
             point_winner = 2 if current_hitter == 1 else 1
             return point_winner, rally_start_time
        ball_z = 0.0
        publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
        current_hitter = 2 if current_hitter == 1 else 1
        time.sleep(0.2 + random.uniform(0, 0.3))
        if hit > 0 and random.random() < OUT_PROBABILITY / 2:
             print("Sim Result: Unforced Error!")
             point_winner = 2 if current_hitter == 2 else 1
             return point_winner, rally_start_time
    print("Sim Result: Rally ended (max hits).")
    point_winner = 2 if current_hitter == 1 else 1
    return point_winner, rally_start_time


# --- Main Game Loop --- (No changes needed here) ---
def main():
    global server, serving_side

    print("--- Starting Tennis Game Simulation ---")
    print(f"Publishing to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")

    publish_mqtt("tennis/scoreboard/reset_clock", "") # Reset clock first
    publish_mqtt("tennis/scoreboard/clock", format_clock(game_time_seconds))
    publish_mqtt("tennis/scoreboard/team1_points", team1_points_str)
    publish_mqtt("tennis/scoreboard/team2_points", team2_points_str)
    publish_mqtt("tennis/scoreboard/team1_games", f"{team1_games},{current_set}")
    publish_mqtt("tennis/scoreboard/team2_games", f"{team2_games},{current_set}")

    try:
        point_count = 0
        while True: # Loop for each point
            point_count += 1
            print(f"\n===== Point #{point_count} Start =====")

            point_winner, rally_start_time = simulate_rally(server, serving_side)

            publish_mqtt("tennis/scoreboard/stop_clock", "")
            publish_final_clock_time(rally_start_time) # Accumulates time for the point just played

            print(f"Point Winner: Player {point_winner}")

            # Update score AND potentially reset clock if game ended
            server, serving_side = update_score(point_winner)

            print("--------------------")
            pause_duration = random.uniform(2.5, 5.0)
            time.sleep(pause_duration)

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user (Ctrl+C).")
        publish_mqtt("tennis/scoreboard/stop_clock", "")
    except Exception as e:
         print(f"\n--- SIMULATION CRASHED ---")
         print(f"Error: {e}")
         import traceback
         print(traceback.format_exc())
    finally:
        print("--- Simulation Ended ---")
        # Note: game_time_seconds reflects time SINCE LAST GAME ended here
        final_time = format_clock(game_time_seconds)
        print(f"Final Accumulated Game Time (since last game reset): {final_time}")


if __name__ == "__main__":
    main()