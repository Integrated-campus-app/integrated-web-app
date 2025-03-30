import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NoticeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("notices", self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"message": "WebSocket Connected!"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notices", self.channel_name)

    async def send_notice(self, event):
        notice = event['notice']
        await self.send(text_data=json.dumps({
            'type': 'notice_update',
            'notice': notice
        }))
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_room"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        username = data["username"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        await self.send(text_data=json.dumps({
            "message": message,
            "username": username
        }))
class NoticeBoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notice_board"

        # Add this WebSocket to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")  # Can be "create", "update", "delete"

        # Broadcast the action and notice data to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_notice",
                "action": action,
                "notice": data.get("notice")
            }
        )

    async def send_notice(self, event):
        """Send notice data to all WebSocket clients"""
        await self.send(text_data=json.dumps({
            "action": event["action"],
            "notice": event["notice"]
        }))