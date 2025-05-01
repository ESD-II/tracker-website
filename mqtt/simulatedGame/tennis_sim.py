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

SIMULATION_SPEED = 0.1  # Seconds between ball position updates
RALLY_LENGTH_MIN = 3    # Min number of hits in a rally
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

# Modify end_point_update_clock: only publish clock value, stop signal sent separately
def publish_final_clock_time(rally_start_time):
    """Calculates rally duration, updates total time, publishes final clock value."""
    global game_time_seconds
    if rally_start_time is None: return # Should not happen if called correctly

    rally_duration = time.monotonic() - rally_start_time
    game_time_seconds += rally_duration

    clock_str = format_clock(game_time_seconds)
    publish_mqtt("tennis/scoreboard/clock", clock_str)
    print(f"Point Duration: {rally_duration:.2f}s. Total Game Time: {clock_str}")

def get_score_index(score_str):
    """Gets the index of a score string in the sequence."""
    try:
        return POINTS_SEQUENCE.index(score_str)
    except ValueError:
        return -1

def update_score(winner):
    """Updates the points, games, and sets based on the point winner."""
    global team1_points_str, team2_points_str, team1_games, team2_games, server, serving_side, current_set
    # Keep track of previous score to detect game/set changes accurately
    prev_t1_games = team1_games
    prev_t2_games = team2_games
    prev_set = current_set

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
    print(f"Score Updated: {team1_points_str}-{team2_points_str}", end='') # Print without newline initially

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
             # current_set += 1 # Increment set if simulating multiple sets
             # Switch server for start of new set (often alternates)
             server = 2 if server == 1 else 1
             # Publish the reset game score for the new set
             publish_mqtt("tennis/scoreboard/team1_games", f"{team1_games},{current_set}")
             publish_mqtt("tennis/scoreboard/team2_games", f"{team2_games},{current_set}")
             print(f"Starting Set {current_set + 1} simulation. Score {team1_games}-{team2_games}. Server: P{server}")
        else: # Game over, but set not over
            # Switch server for the next game
            server = 2 if server == 1 else 1
            print(f" | Next Server: P{server}")

    else: # Point over, but game not over
        # Update serving side
        if team1_points_str == "40" and team2_points_str == "40": # Just reached Deuce
            serving_side = "deuce"
        elif team1_points_str == "AD" or team2_points_str == "AD": # Advantage score
             serving_side = "ad"
        else: # Any other score (0, 15, 30) alternates
            serving_side = "ad" if serving_side == "deuce" else "deuce"
        print(f" | Server: P{server} ({serving_side})") # Print rest of score line

    # Return server state explicitly for potential use if needed
    return server, serving_side


def point_won(type, winner):
     # This function might become redundant if logic moved into update_score,
     # but kept for now if called elsewhere (it wasn't in the provided code).
     # Ensure consistency with update_score logic if kept.
    print(f"WARNING: point_won called - logic should be in update_score.")
    pass

def get_serve_position(current_server, current_serving_side):
    """Determines the ball's starting position for a serve."""
    # Use passed-in state
    x_pos = -COURT_LENGTH / 2 if current_server == 1 else COURT_LENGTH / 2
    y_pos = -COURT_WIDTH_SINGLES * 0.25 if current_serving_side == "deuce" else COURT_WIDTH_SINGLES * 0.25
    z_pos = 1.5
    return x_pos, y_pos, z_pos

def is_out_of_bounds(x, y, z):
    """Checks if the ball coordinates are out of bounds (basic floor check)."""
    if z < 0: # Check only when it hits the ground (or goes below)
        if abs(x) > COURT_LENGTH / 2 or abs(y) > COURT_WIDTH_SINGLES / 2:
             # print(f"Debug: Ball OUT at ({x:.2f}, {y:.2f}) on bounce!")
             return True
        else:
             # print(f"Debug: Ball IN at ({x:.2f}, {y:.2f}) on bounce!")
             return False
    return False # Still in the air


def simulate_rally(current_server, current_serving_side):
    """Simulates the ball movement for one point and returns the point winner (1 or 2)."""
    global ball_x, ball_y, ball_z # Allow modification of global ball state

    # --- Point Start ---
    rally_start_time = time.monotonic()
    publish_mqtt("tennis/scoreboard/start_clock", "") # Signal clock start
    point_winner = 0

    # 1. Serve Setup
    ball_x, ball_y, ball_z = get_serve_position(current_server, current_serving_side)
    print(f"\n--- Simulating Point --- Server: P{current_server} ({current_serving_side})")
    # print(f"Serve Start Pos: ({ball_x:.2f}, {ball_y:.2f}, {ball_z:.2f})")
    publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
    time.sleep(0.5) # Shorter pause before serve

    # Serve Trajectory
    target_x_factor = 0.3
    target_x = (COURT_LENGTH * target_x_factor) if current_server == 1 else (-COURT_LENGTH * target_x_factor)
    target_y = -COURT_WIDTH_SINGLES * 0.25 if current_serving_side == "deuce" else COURT_WIDTH_SINGLES * 0.25
    dx = target_x - ball_x
    dy = target_y - ball_y
    dist_serve = math.sqrt(dx**2 + dy**2) or 1

    # Simulate serve flight
    steps = 15
    # print("Sim: Serving...")
    serve_fault = False
    for i in range(1, steps + 1):
        frac = i / steps
        ball_x += dx / steps
        ball_z = 1.5 + math.sin(frac * math.pi) * 1.5 # Simple arc
        ball_y += dy / steps
        publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
        time.sleep(SIMULATION_SPEED / 2.5) # Slightly faster serve anim

        # Net check during serve
        if abs(ball_x) < 0.5 and ball_z < NET_HEIGHT:
             print("Sim Result: Fault (Hit Net)")
             serve_fault = True
             break

    # Check serve landing
    if not serve_fault:
        landed_in_correct_half = (current_server == 1 and ball_x > 0) or (current_server == 2 and ball_x < 0)
        landed_within_sidelines = abs(ball_y) <= COURT_WIDTH_SINGLES / 2
        landed_within_baseline = abs(ball_x) <= COURT_LENGTH / 2
        landed_in_service_area = abs(ball_x) < SERVICE_BOX_DEPTH # Crude check
        if not (landed_in_correct_half and landed_within_sidelines and landed_within_baseline and landed_in_service_area):
            print("Sim Result: Fault (Serve Out)")
            serve_fault = True

    if serve_fault:
        publish_mqtt("tennis/scoreboard/ball_crossed_line", "1") # Signal fault
        time.sleep(0.5)
        point_winner = 2 if current_server == 1 else 1 # Server loses point on fault (simplification)
        # Return winner and start time - clock stop handled in main loop now
        return point_winner, rally_start_time

    # --- Serve IN ---
    # print("Sim: Serve in!")
    ball_z = 0.0 # Land ball
    publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
    time.sleep(0.1)

    current_hitter = 2 if current_server == 1 else 1 # Receiver hits first

    # 2. Rally
    num_hits = random.randint(RALLY_LENGTH_MIN, RALLY_LENGTH_MAX)
    # print(f"Sim: Rallying (max {num_hits} hits)...")

    for hit in range(num_hits):
        # print(f"Sim Hit {hit+1}: P{current_hitter}...")
        target_x_side = -COURT_LENGTH / 2 if current_hitter == 2 else COURT_LENGTH / 2
        target_x_rel = random.uniform(0.1, 0.45)
        target_x = target_x_side * (1 - target_x_rel) if target_x_side < 0 else target_x_side * target_x_rel
        target_y = random.uniform(-COURT_WIDTH_SINGLES/2 * 0.95, COURT_WIDTH_SINGLES/2 * 0.95)
        start_x, start_y, start_z = ball_x, ball_y, 0.1 # Hit from near ground

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

            if (prev_x * ball_x <= 0): # Crossed net line approx
                 if ball_z < NET_HEIGHT:
                     print("Sim Result: Net!")
                     hit_net = True
                     break

        if hit_net:
             publish_mqtt("tennis/scoreboard/ball_crossed_line", "1") # Signal error
             point_winner = 2 if current_hitter == 1 else 1 # Hitter loses
             return point_winner, rally_start_time # Return winner and start time

        # Check if landed OUT (using z slightly below 0)
        if is_out_of_bounds(ball_x, ball_y, -0.01):
             print("Sim Result: Out!")
             publish_mqtt("tennis/scoreboard/ball_crossed_line", "1") # Signal error
             point_winner = 2 if current_hitter == 1 else 1 # Hitter loses
             return point_winner, rally_start_time # Return winner and start time

        # --- Ball IN ---
        # print("Sim: In!")
        ball_z = 0.0 # Land ball
        publish_mqtt("tennis/scoreboard/ball_coords", f"{ball_x:.2f},{ball_y:.2f},{ball_z:.2f}")
        current_hitter = 2 if current_hitter == 1 else 1 # Switch hitter
        time.sleep(0.2 + random.uniform(0, 0.3)) # Shorter reaction pause

        # Random unforced error chance
        if hit > 0 and random.random() < OUT_PROBABILITY / 2:
             print("Sim Result: Unforced Error!")
             # Player whose turn it WAS made the error
             point_winner = 2 if current_hitter == 2 else 1 # Opponent wins
             # Don't signal ball_crossed_line for unforced error unless desired
             return point_winner, rally_start_time # Return winner and start time

    # --- Max hits reached ---
    print("Sim Result: Rally ended (max hits).")
    # Player who just hit successfully wins the point (opponent didn't return)
    point_winner = 2 if current_hitter == 1 else 1
    return point_winner, rally_start_time # Return winner and start time


# --- Main Game Loop ---

def main():
    global server, serving_side # Allow modification by update_score

    print("--- Starting Tennis Game Simulation ---")
    # Use configured broker/port from top
    print(f"Publishing to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")

    # --- Initial State Publish ---
    publish_mqtt("tennis/scoreboard/reset_clock", "") # Reset clock first
    publish_mqtt("tennis/scoreboard/clock", format_clock(game_time_seconds))
    publish_mqtt("tennis/scoreboard/team1_points", team1_points_str)
    publish_mqtt("tennis/scoreboard/team2_points", team2_points_str)
    publish_mqtt("tennis/scoreboard/team1_games", f"{team1_games},{current_set}")
    publish_mqtt("tennis/scoreboard/team2_games", f"{team2_games},{current_set}")
    # Optionally publish initial server if tracked/needed by frontend
    # publish_mqtt("tennis/scoreboard/server", server)

    try:
        point_count = 0
        while True: # Loop for each point
            point_count += 1
            print(f"\n===== Point #{point_count} Start =====")

            # --- Simulate one point (serves + rally) ---
            # Pass current server state to the simulation function
            point_winner, rally_start_time = simulate_rally(server, serving_side)

            # --- Point Finished ---
            # Send stop signal explicitly *after* rally simulation concludes
            publish_mqtt("tennis/scoreboard/stop_clock", "")
            # Update and publish final clock time for the point
            publish_final_clock_time(rally_start_time)

            print(f"Point Winner: Player {point_winner}")

            # --- Update Score State ---
            # update_score now returns the possibly updated server/serving_side
            server, serving_side = update_score(point_winner)

            # --- Pause between points ---
            print("--------------------")
            pause_duration = random.uniform(2.5, 5.0)
            # print(f"Pausing for {pause_duration:.1f}s...")
            time.sleep(pause_duration)

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user (Ctrl+C).")
        # Attempt to publish a final stop clock on interrupt
        publish_mqtt("tennis/scoreboard/stop_clock", "")
    except Exception as e:
         print(f"\n--- SIMULATION CRASHED ---")
         print(f"Error: {e}")
         import traceback
         print(traceback.format_exc())
         # Optionally publish stop clock on crash too
         # publish_mqtt("tennis/scoreboard/stop_clock", "")
    finally:
        print("--- Simulation Ended ---")
        final_time = format_clock(game_time_seconds)
        print(f"Final Accumulated Game Time: {final_time}")


if __name__ == "__main__":
    main()