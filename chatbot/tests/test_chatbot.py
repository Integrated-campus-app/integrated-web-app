import os
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from pathlib import Path
from chatbot.models import Conversation, Message
from chatbot.llm_integration import LLMIntegration
from chatbot.knowledge_base.processor import KnowledgeBaseProcessor

class ChatbotTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.llm = LLMIntegration()
        self.kb_processor = KnowledgeBaseProcessor()
        
        # Create test conversation
        self.conversation = Conversation.objects.create(
            title="Test Conversation"
        )
        
        # Create test messages
        self.messages = [
            Message.objects.create(
                conversation=self.conversation,
                content="Hello, how can I help you?",
                role="assistant"
            ),
            Message.objects.create(
                conversation=self.conversation,
                content="What are the key features?",
                role="user"
            )
        ]

    def test_conversation_creation(self):
        """Test creating a new conversation."""
        url = reverse('conversation-list')
        data = {'title': 'New Test Conversation'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_message_creation(self):
        """Test creating a new message."""
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'Test message',
            'role': 'user'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 3)

    def test_message_status_update(self):
        """Test updating message status."""
        message = self.messages[0]
        url = reverse('message-detail', args=[message.id])
        data = {'status': 'delivered'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertEqual(message.status, 'delivered')

    def test_conversation_archiving(self):
        """Test archiving a conversation."""
        url = reverse('conversation-detail', args=[self.conversation.id])
        data = {'is_archived': True}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_archived)

    def test_knowledge_base_search(self):
        """Test searching the knowledge base."""
        # Create a test document
        test_doc = Path('test_doc.txt')
        test_doc.write_text('This is a test document about chatbot features.')
        
        try:
            # Add document to knowledge base
            result = self.llm.add_to_knowledge_base(str(test_doc))
            self.assertEqual(result['status'], 'success')
            
            # Search knowledge base
            results = self.kb_processor.search('chatbot features')
            self.assertTrue(len(results) > 0)
            self.assertTrue(any('chatbot features' in r['text'].lower() for r in results))
            
        finally:
            # Clean up test document
            test_doc.unlink()

    def test_llm_integration(self):
        """Test LLM integration."""
        messages = [
            {"role": "user", "content": "What are the key features?"}
        ]
        
        response = self.llm.generate_response(messages)
        self.assertIn('content', response)
        self.assertIn('model', response)
        self.assertIn('usage', response)

    def test_message_attachments(self):
        """Test message attachments."""
        url = reverse('message-list')
        data = {
            'conversation': self.conversation.id,
            'content': 'Message with attachment',
            'role': 'user',
            'attachments': json.dumps([
                {
                    'name': 'test.txt',
                    'type': 'text/plain',
                    'size': 100
                }
            ])
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = Message.objects.latest('created_at')
        self.assertTrue(message.attachments)

    def test_error_handling(self):
        """Test error handling in message processing."""
        # Test with invalid conversation ID
        url = reverse('message-list')
        data = {
            'conversation': 99999,  # Non-existent ID
            'content': 'Test message',
            'role': 'user'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_message_retry(self):
        """Test message retry functionality."""
        message = self.messages[0]
        message.status = 'error'
        message.error_message = 'Test error'
        message.save()
        
        url = reverse('message-retry', args=[message.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertEqual(message.status, 'sent')
        self.assertEqual(message.retry_count, 1) 