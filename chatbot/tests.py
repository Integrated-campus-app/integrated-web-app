from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Conversation, Message
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class ChatbotTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test conversation
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )

    def test_create_conversation(self):
        """Test creating a new conversation"""
        url = reverse('conversation-list')
        data = {'title': 'New Test Conversation'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_send_message(self):
        """Test sending a message and getting response"""
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'What are the office hours?'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('data: ' in response.content.decode())

    def test_get_conversation_messages(self):
        """Test retrieving messages from a conversation"""
        # Create test messages
        Message.objects.create(
            conversation=self.conversation,
            content='Test message 1',
            is_user=True
        )
        Message.objects.create(
            conversation=self.conversation,
            content='Test response 1',
            is_user=False
        )

        url = reverse('conversation-messages', args=[self.conversation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_conversation(self):
        """Test deleting a conversation"""
        url = reverse('conversation-detail', args=[self.conversation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Conversation.objects.get(id=self.conversation.id).is_deleted)

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'Test message'
        }
        
        # Send multiple requests quickly
        for _ in range(11):  # Assuming rate limit is 10
            response = self.client.post(url, data, format='json')
        
        # The last request should be rate limited
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_knowledge_base_integration(self):
        """Test knowledge base integration"""
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'What are the course requirements for CS101?'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response contains source information
        response_content = response.content.decode()
        self.assertTrue('source_hint' in response_content)

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        url = reverse('message-list')
        data = {
            'conversation': 99999,  # Non-existent conversation
            'content': 'Test message'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_conversation_context(self):
        """Test conversation context in responses"""
        # Create a conversation with multiple messages
        messages = [
            ('What are the office hours?', True),
            ('Office hours are 9-5.', False),
            ('What about weekends?', True)
        ]
        
        for content, is_user in messages:
            Message.objects.create(
                conversation=self.conversation,
                content=content,
                is_user=is_user
            )

        # Send a follow-up question
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'And holidays?'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the response considers conversation context
        response_content = response.content.decode()
        self.assertTrue('data: ' in response_content)
