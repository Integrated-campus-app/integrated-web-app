import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Question, Answer

class QuestionConsumer(AsyncWebsocketConsumer):
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
            answer = await self.create_answer(data['answer'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_answer',
                    'answer': answer
                }
            )

    async def send_answer(self, event):
        await self.send(text_data=json.dumps({
            'answer': event['answer']
        }))

    @database_sync_to_async
    def create_answer(self, answer_data):
        question = Question.objects.get(id=self.question_id)
        answer = Answer.objects.create(
            question=question,
            content=answer_data['content'],
            user=answer_data['user']
        )
        return {
            'id': answer.id,
            'content': answer.content,
            'created_at': answer.created_at.isoformat(),
            'user': {
                'id': answer.user.id,
                'username': answer.user.username
            }
        }