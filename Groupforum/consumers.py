from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept all connections without authentication
        await self.accept()
        # Add to a general notifications group
        await self.channel_layer.group_add(
            "notifications",
            self.channel_name
        )

    async def disconnect(self, close_code):
        # Remove from group when disconnected
        await self.channel_layer.group_discard(
            "notifications",
            self.channel_name
        )

    async def send_notification(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))