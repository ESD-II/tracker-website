# backend/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Define the group name used for broadcasting updates
# Needs to be the same as CHANNEL_GROUP_NAME in run_mqtt_bridge.py
CHANNEL_GROUP_NAME = 'tennis_updates'

class BallTrackerConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for the tennis tracker.
    Connects clients to the 'tennis_updates' group to receive
    live coordinates and signals pushed from the MQTT bridge.
    """
    async def connect(self):
        """Called when the WebSocket is trying to connect."""
        self.room_group_name = CHANNEL_GROUP_NAME

        # Join the room group
        # Uses the channel layer configured in settings.py (e.g., Redis)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name  # Unique name for this specific connection
        )

        # Accept the WebSocket connection
        await self.accept()
        print(f"WebSocket accepted: {self.channel_name} joined group {self.room_group_name}")

    async def disconnect(self, close_code):
        """Called when the WebSocket closes for any reason."""
        print(f"WebSocket disconnected: {self.channel_name} leaving group {self.room_group_name}, code={close_code}")
        # Leave the room group
        if hasattr(self, 'room_group_name'): # Ensure group name exists before leaving
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Optional: Handle messages *received from* the WebSocket client
    # async def receive(self, text_data):
    #     """
    #     Called when a message is received from the WebSocket client.
    #     We don't expect messages from the client in this use case.
    #     """
    #     print(f"Received message from WebSocket {self.channel_name}: {text_data}")
    #     # Example: Echo back
    #     # text_data_json = json.loads(text_data)
    #     # message = text_data_json['message']
    #     # await self.send(text_data=json.dumps({'message': message}))
    #     pass

    # **** THIS IS THE CRITICAL METHOD ****
    async def tracker_update(self, event):
        """
        Handler for messages sent over the channel layer to the group.
        This method name ('tracker_update') MUST match the 'type'
        specified in the group_send call in run_mqtt_bridge.py.

        Receives data from the MQTT bridge (via Redis) and sends it
        down the WebSocket to the connected browser client.
        """
        message_data = event['data'] # Extract the data payload sent by the bridge

        # Send the received data as a JSON string to the WebSocket client
        await self.send(text_data=json.dumps(message_data))
        # print(f"Sent tracker_update to WebSocket {self.channel_name}") # Optional debug log