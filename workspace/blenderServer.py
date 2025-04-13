import bpy
import numpy as np
import socket
import struct
import math
import threading
import queue
import json
from mathutils import Euler

# === Global Variables for the Server ===
server_socket = None
client_threads = []
command_queue = queue.Queue()  # Thread-safe queue for requests
server_running = False
server_thread = None

# === Blender Node Setup for Render Preview ===
# Enable node-based compositing and clear default nodes
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
for n in tree.nodes:
    tree.nodes.remove(n)

# Create input render layer node and output viewer node
rl = tree.nodes.new('CompositorNodeRLayers')
rl.location = (185, 285)
viewer_node = tree.nodes.new('CompositorNodeViewer')
viewer_node.location = (750, 210)
viewer_node.use_alpha = False
tree.links.new(rl.outputs[0], viewer_node.inputs[0])

# === Utility Functions ===

def xform_object_by_name(object_name, x, y, z, pitch, roll, yaw):
    """Move and rotate the specified object if found."""
    if object_name in bpy.data.objects:
        obj = bpy.data.objects[object_name]
        obj.location = (x, y, z)
        # Convert degrees to radians for Euler angles
        obj.rotation_euler = Euler((math.radians(pitch),
                                    math.radians(roll),
                                    math.radians(yaw)), 'XYZ')
    else:
        print(f"Object '{object_name}' not found.")

def xform_camera_by_name(camera_name, x, y, z, pitch, roll, yaw):
    """Move and rotate the specified camera if found."""
    if camera_name in bpy.data.objects:
        cam = bpy.data.objects[camera_name]
        cam.location = (x, y, z)
        cam.rotation_euler = Euler((math.radians(pitch),
                                    math.radians(roll),
                                    math.radians(yaw)), 'XYZ')
    else:
        print(f"Camera '{camera_name}' not found.")

def set_camera_focal_length(camera_name, focal_length):
    """Set focal length for the specified camera."""
    if camera_name in bpy.data.objects and bpy.data.objects[camera_name].type == 'CAMERA':
        bpy.data.objects[camera_name].data.lens = focal_length
    else:
        print(f"Camera '{camera_name}' not found or not a valid camera.")

# === Server Connection Handling ===

def client_handler(conn, addr):
    """
    Reads JSON messages (each terminated by a newline) from this client.
    Each message should be a JSON object with at least a key 'command' that is either
    "move" or "render". The remaining keys depend on the command.
    """
    print(f"Client connected from {addr}")
    try:
        # Wrap the socket in a file-like object to conveniently read lines.
        file_obj = conn.makefile(mode='r')
        while server_running:
            line = file_obj.readline()  # reads until newline
            if not line:
                break  # Connection closed
            try:
                data = json.loads(line)
                # Place a tuple (connection, data) on the command queue.
                command_queue.put((conn, data))
            except json.JSONDecodeError as e:
                print("JSON decode error:", e)
    except Exception as e:
        print("Exception in client handler:", e)
    finally:
        print(f"Client from {addr} disconnected.")
        try:
            conn.close()
        except Exception:
            pass

def server_listener(host='0.0.0.0', port=55001):
    """Listener thread that accepts client connections and spawns handler threads."""
    global server_socket, server_running, client_threads
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    server_socket.settimeout(1.0)
    print(f"Server listening on {host}:{port}")
    while server_running:
        try:
            conn, addr = server_socket.accept()
            t = threading.Thread(target=client_handler, args=(conn, addr), daemon=True)
            t.start()
            client_threads.append(t)
        except socket.timeout:
            continue
        except Exception as e:
            print("Exception in server_listener:", e)
            break

def start_network_server(host='0.0.0.0', port=55001):
    """Starts the network listener in a separate thread and registers the timer in Blender."""
    global server_running, server_thread
    if server_running:
        print("Server already running.")
        return
    server_running = True
    server_thread = threading.Thread(target=server_listener, args=(host, port), daemon=True)
    server_thread.start()
    bpy.app.timers.register(process_commands, first_interval=0.1)
    print("Network server started.")

def stop_network_server():
    """Stops the server, the listener, and active client threads."""
    global server_running, server_socket
    server_running = False
    if server_socket:
        try:
            server_socket.close()
        except Exception:
            pass
    print("Waiting for client threads to finish...")
    for t in client_threads:
        t.join(timeout=1.0)
    print("Server stopped.")

# === Main Timer Callback for Processing Commands ===

def process_commands():
    """
    Called repeatedly from Blender's main thread.
    It checks the command_queue and processes all waiting commands.
    """
    # Process all commands currently queued
    while not command_queue.empty():
        try:
            conn, data = command_queue.get_nowait()
        except queue.Empty:
            break

        # Data is expected to be a dict with a 'command' key.
        cmd_type = data.get("command")
        if cmd_type == "move":
            # Expected keys: "name", "x", "y", "z", "pitch", "roll", "yaw"
            name = data.get("name")
            x = data.get("x", 0)
            y = data.get("y", 0)
            z = data.get("z", 0)
            pitch = data.get("pitch", 0)
            roll = data.get("roll", 0)
            yaw = data.get("yaw", 0)
            print(f"Moving object '{name}' to ({x}, {y}, {z}) with rotation ({pitch}, {roll}, {yaw})")
            xform_object_by_name(name, x, y, z, pitch, roll, yaw)
            # Optionally send an acknowledgement (here we send a simple string)
            try:
                conn.sendall("ACK_MOVE\n".encode("utf-8"))
            except Exception as e:
                print("Error sending ACK_MOVE:", e)

        elif cmd_type == "render":
            # Expected keys: "camera" (camera name),
            # "x", "y", "z", "pitch", "roll", "yaw", optionally "resolution" and "focal_length"
            camera = data.get("camera")
            x = data.get("x", 0)
            y = data.get("y", 0)
            z = data.get("z", 0)
            pitch = data.get("pitch", 0)
            roll = data.get("roll", 0)
            yaw = data.get("yaw", 0)
            resolution = data.get("resolution", None)  # e.g. [width, height]
            focal_length = data.get("focal_length", None)
            print(f"Render request from camera '{camera}' at position ({x}, {y}, {z}) with rotation ({pitch}, {roll}, {yaw})")
            
            # If resolution is provided update scene render resolution
            if resolution and isinstance(resolution, (list, tuple)) and len(resolution) == 2:
                bpy.context.scene.render.resolution_x = int(resolution[0])
                bpy.context.scene.render.resolution_y = int(resolution[1])
            # Update camera transform
            xform_camera_by_name(camera, x, y, z, pitch, roll, yaw)
            # Optionally set focal length if provided
            if focal_length:
                set_camera_focal_length(camera, focal_length)
            # Render the scene
            bpy.ops.render.render()
            # Obtain pixel data from the Viewer Node (assumes node setup as above)
            pixels = bpy.data.images.get('Viewer Node').pixels[:]
            arr = np.array(pixels)
            # Convert the raw [0,1] float values to 8-bit values (without gamma correction)
            pixel_bytes = np.uint8(np.clip(arr, 0, 1) * 255)
            # Remove the alpha channel so we have RGB only.
            num_pixels = len(pixel_bytes) // 4
            pixel_bytes = pixel_bytes.reshape((num_pixels, 4))[:, :3]
            pixel_data = pixel_bytes.flatten().tobytes()
            # Send the length of the data first (4-byte integer in network byte order)
            try:
                data_length = struct.pack("!I", len(pixel_data))
                conn.sendall(data_length + pixel_data)
            except Exception as e:
                print("Error sending render image:", e)
        else:
            print("Unknown command received:", data)
    # Continue processing if the server is running
    return 0.1 if server_running else None

# === Blender UI Operators and Panel ===

class SERVER_OT_Start(bpy.types.Operator):
    bl_idname = "scene.start_server"
    bl_label = "Start Server"

    def execute(self, context):
        start_network_server(host='0.0.0.0', port=55001)
        self.report({'INFO'}, "Server started")
        return {'FINISHED'}

class SERVER_OT_Stop(bpy.types.Operator):
    bl_idname = "scene.stop_server"
    bl_label = "Stop Server"

    def execute(self, context):
        stop_network_server()
        self.report({'INFO'}, "Server stopped")
        return {'FINISHED'}

class SERVER_PT_Panel(bpy.types.Panel):
    bl_idname = "_PT_MulticlientServer"
    bl_label = "Multiclient Server"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MultiServer"

    def draw(self, context):
        layout = self.layout
        layout.operator("scene.start_server", text="Start Server")
        layout.operator("scene.stop_server", text="Stop Server")

def register():
    bpy.utils.register_class(SERVER_OT_Start)
    bpy.utils.register_class(SERVER_OT_Stop)
    bpy.utils.register_class(SERVER_PT_Panel)

def unregister():
    bpy.utils.unregister_class(SERVER_PT_Panel)
    bpy.utils.unregister_class(SERVER_OT_Stop)
    bpy.utils.unregister_class(SERVER_OT_Start)

if __name__ == "__main__":
    register()
    # Optionally you can start the server automatically here:
    start_network_server(host='0.0.0.0', port=55001)
    # Comment out the above line when using on local machine with gui