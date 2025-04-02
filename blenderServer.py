import bpy
import numpy as np
import socket
import struct
from mathutils import Euler
import math
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

counter = 1
conn = []
s = []
connected = False

# Switch on nodes
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links

# Clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)

# Create input render layer node
rl = tree.nodes.new('CompositorNodeRLayers')      
rl.location = 185, 285

# Create output node
v = tree.nodes.new('CompositorNodeViewer')   
v.location = 750, 210
v.use_alpha = False

# Links
links.new(rl.outputs[0], v.inputs[0])  # link Image output to Viewer input

def xform_object_by_name(object_name, x, y, z, pitch, roll, yaw):
    if object_name in bpy.data.objects:
        obj = bpy.data.objects[object_name]
        obj.location = (x, y, z)
        obj.rotation_euler = Euler((math.radians(pitch), math.radians(roll), math.radians(yaw)), 'XYZ')
        logger.debug(f"Transformed object '{object_name}' to position ({x}, {y}, {z}) with rotation ({pitch}, {roll}, {yaw})")
    else:
        logger.warning(f"Object '{object_name}' not found.")


def handle_data():
    global conn, connected

    if not connected or conn is None:
        return None

    interval = 0.1  # Timer interval

    try:
        # Receive 32 bytes (8 floats: width, height, x, y, z, pitch, roll, yaw)
        data = conn.recv(32)
        if not data or len(data) != 32:
            logger.error(f"Received incorrect data size: {len(data) if data else 0} (expected 32 bytes)")
            return None
        floats = struct.unpack('f' * 8, data)
        
        # Parse the floats
        width, height = int(floats[0]), int(floats[1])
        x, y, z, pitch, roll, yaw = floats[2:]

        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
        logger.debug(f"Set render resolution to {width}x{height}")

        # Receive object name length
        object_name_length = struct.unpack('I', conn.recv(4))[0]
        
        # Receive the object name string
        object_name = conn.recv(object_name_length).decode('utf-8')
        logger.debug(f"Received object name: {object_name}")

        # Transform the object
        xform_object_by_name(object_name, x, y, z, pitch, roll, yaw)

        # Render the scene
        bpy.ops.render.render()

        # Retrieve and send pixel data
        pixels = bpy.data.images['Viewer Node'].pixels
        arr = np.array(pixels[:])
        pixel_data = np.uint8(arr * 255.0)

        conn.sendall(pixel_data)  # Send the image back to MATLAB
        logger.debug("Sent pixel data to client.")

    except (socket.error, OSError, struct.error) as e:
        logger.error(f"Error during data handling: {e}")
        stop_server()
        return None

    return interval

def stop_server():
    global conn, s, connected
    connected = False
    bpy.app.timers.unregister(handle_data)
    if conn:
        conn.close()
        conn = None
    if s:
        s.close()
        s = None
    logger.info("Server stopped and disconnected.")
    
 ###################################################   
    
def capture_image(camera_name):
    """ Renders the scene from a specified camera and returns the image as base64. """
    if camera_name not in bpy.data.objects:
        logger.warning(f"Camera '{camera_name}' not found.")
        return None

    # Set active camera
    bpy.context.scene.camera = bpy.data.objects[camera_name]

    # Render the scene
    bpy.ops.render.render()

    # Convert the rendered image to base64
    image = bpy.data.images['Viewer Node']
    pixels = np.array(image.pixels[:])
    pixels = (pixels * 255).astype(np.uint8)

    # Save to buffer
    buf = BytesIO()
    buf.write(bytes(pixels))
    buf.seek(0)

    # Encode as base64
    return base64.b64encode(buf.read()).decode('utf-8')

async def websocket_handler(websocket, path):
    """ Handles incoming WebSocket connections and messages. """
    global connected_clients
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            logger.info(f"Received WebSocket message: {message}")

            if message.startswith("CAMERA:"):
                camera_name = message.split(":")[1]
                img_data = capture_image(camera_name)
                if img_data:
                    await websocket.send(img_data)

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket client disconnected.")
    finally:
        connected_clients.remove(websocket)

async def start_websocket_server():
    """ Starts the WebSocket server. """
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    logger.info("WebSocket server started on ws://0.0.0.0:8765")
    await server.wait_closed()

# Start WebSocket server in Blender
def start_ws_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server())

# Register the WebSocket server when Blender starts
bpy.app.timers.register(start_ws_server, first_interval=1.0)    
    
#################################################################
class TEST_OT_stopServer(bpy.types.Operator):
    bl_idname = "scene.stop_server"
    bl_label = "Stop Server"

    def execute(self, context):
        stop_server()
        return {'FINISHED'}

class TEST_OT_startServer(bpy.types.Operator):
    bl_idname = "scene.start_server"
    bl_label = "Start Server"

    def execute(self, context):
        global s, conn, connected
        logger.info("Starting server...")
        HOST = '127.0.0.1'
        PORT = 55001

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen()
        logger.info(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        conn.settimeout(3600)
        connected = True
        logger.info(f"Connection established with {addr}")
        bpy.app.timers.register(handle_data)
        return {'FINISHED'}

class MatlabPanel(bpy.types.Panel):
    bl_label = "Matlab Server"
    bl_idname = "PT_MatlabPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Matlab Server"
    
    def draw(self, context):
        layout = self.layout
        row1 = layout.row()
        row1.operator("scene.start_server", text="Start Server")
        row2 = layout.row()
        row2.operator("scene.stop_server", text="Stop Server")

def register():
    bpy.utils.register_class(MatlabPanel)
    bpy.utils.register_class(TEST_OT_stopServer)
    bpy.utils.register_class(TEST_OT_startServer)

def unregister():
    bpy.utils.unregister_class(MatlabPanel)
    bpy.utils.unregister_class(TEST_OT_stopServer)
    bpy.utils.unregister_class(TEST_OT_startServer)

if __name__ == "__main__":
    register()
