
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth.models import AnonymousUser


from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .llm_integration import generate_response

class ChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

async def receive(self, text_data):
    try:
        data = json.loads(text_data)
        user_query = data["message"]
        
        if not user_query.strip():
            await self.send(json.dumps({"error": "Empty query"}))
            return

        response = generate_response(user_query)
        if not response:
            await self.send(json.dumps({"error": "Knowledge base not loaded"}))
            return

        # ... streaming logic ...
    except Exception as e:
        await self.send(json.dumps({"error": str(e)}))# Typing effect

class QAConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.question_id = self.scope['url_route']['kwargs']['question_id']
        self.room_group_name = f'question_{self.question_id}'
        
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
        if data['type'] == 'new_answer':
            await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_answer',
                'answer': data['answer'],
                'sender_id': str(self.scope["user"].id),
                'question_user_id': data['answer']['question_user_id']  # Now available
            }
        )

        # Notify question author only
        await self.channel_layer.group_send(
            f"user_{data['answer']['question_user_id']}",  # Requires question_user_id in answer data
            {
                'type': 'send_notification',
                'message': f"New answer on your question: {data['answer']['content'][:50]}..."
            }
        )

    async def send_answer(self, event):
        await self.send(text_data=json.dumps(event))
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authenticate user (reject if not logged in)
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return

        await self.accept()
        user_id = str(self.scope["user"].id)
        
        # Add user to personal and global notification groups
        await self.channel_layer.group_add(
            f"user_{user_id}",  # For personal notifications
            self.channel_name
        )
        await self.channel_layer.group_add(
            "global_notifications",  # For broadcast announcements
            self.channel_name
        )

    async def disconnect(self, close_code):
        if hasattr(self.scope["user"], 'id'):
            user_id = str(self.scope["user"].id)
            await self.channel_layer.group_discard(
                f"user_{user_id}",
                self.channel_name
            )
            await self.channel_layer.group_discard(
                "global_notifications",
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': event.get('type', 'notification'),
            'message': event['message'],
            'timestamp': event.get('timestamp')
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authenticate and validate room ID
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return

        self.room_id = self.scope['url_route']['kwargs'].get('room_id', 'general')
        self.room_group_name = f"chat_{self.room_id}"

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
        try:
            data = json.loads(text_data)
            message = data['message']
            
            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': str(self.scope["user"].id),
                    'sender_name': self.scope["user"].username,
                    'timestamp': data.get('timestamp')
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event.get('timestamp')
        }))