from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging
import json
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .llm_integration import generate_response, stream_response, process_message, load_knowledge_base
from .utils import validate_attachment
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

logger = logging.getLogger(__name__)

class BaseViewSet(viewsets.ModelViewSet):
    """Base ViewSet with CORS headers and common functionality."""
    
    def finalize_response(self, request, *args, **kwargs):
        response = super().finalize_response(request, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

class ConversationViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            is_deleted=False,
            user=self.request.user
        ).order_by('-updated_at')

    def list(self, request, *args, **kwargs):
        try:
            conversations = self.get_queryset()
            serializer = self.get_serializer(conversations, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data,
                'count': conversations.count()
            })
        except Exception as e:
            logger.error(f"Error fetching conversations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch conversations',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            conversation = serializer.save(user=request.user)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to create conversation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            conversation = self.get_object()
            messages = conversation.messages.filter(is_deleted=False)
            serializer = MessageSerializer(messages, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data,
                'count': messages.count()
            })
        except ObjectDoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Conversation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch messages',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        try:
            conversation = self.get_object()
            conversation.archive()
            return Response({
                'status': 'success',
                'message': 'Conversation archived successfully'
            })
        except Exception as e:
            logger.error(f"Error archiving conversation: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to archive conversation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        try:
            conversation = self.get_object()
            conversation.restore()
            return Response({
                'status': 'success',
                'message': 'Conversation restored successfully'
            })
        except Exception as e:
            logger.error(f"Error restoring conversation: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to restore conversation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        conversation = self.get_object()
        conversation.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id)
        return Message.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            # Validate message content
            content = request.data.get('content', '').strip()
            if not content:
                return Response({
                    'status': 'error',
                    'message': 'Message content cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate conversation exists
            conversation_id = request.data.get('conversation')
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=request.user,
                    is_deleted=False
                )
            except Conversation.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Conversation not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Handle attachments
            attachments = request.data.get('attachments', [])
            if attachments:
                for attachment in attachments:
                    if not validate_attachment(attachment):
                        return Response({
                            'status': 'error',
                            'message': 'Invalid attachment'
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Create message
            message_data = {
                'conversation': conversation.id,
                'content': content,
                'is_user': True,
                'attachments': attachments
            }
            serializer = self.get_serializer(data=message_data)
            serializer.is_valid(raise_exception=True)
            message = serializer.save()

            # Generate bot response
            try:
                bot_response = generate_response(content, conversation)
                bot_message = Message.objects.create(
                    conversation=conversation,
                    content=bot_response,
                    is_user=False,
                    status='delivered'
                )
                bot_serializer = self.get_serializer(bot_message)
                
                return Response({
                    'status': 'success',
                    'data': {
                        'user_message': serializer.data,
                        'bot_message': bot_serializer.data
                    }
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                message.update_status('error', str(e))
                logger.error(f"Error generating bot response: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': 'Failed to generate bot response',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to create message',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        try:
            message = self.get_object()
            message.mark_as_read()
            return Response({
                'status': 'success',
                'message': 'Message marked as read'
            })
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to mark message as read',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        try:
            message = self.get_object()
            if message.status != 'error':
                return Response({
                    'status': 'error',
                    'message': 'Only failed messages can be retried'
                }, status=status.HTTP_400_BAD_REQUEST)

            message.retry_failed()
            # Attempt to regenerate bot response
            try:
                bot_response = generate_response(message.content, message.conversation)
                new_message = Message.objects.create(
                    conversation=message.conversation,
                    content=bot_response,
                    is_user=False,
                    status='delivered'
                )
                return Response({
                    'status': 'success',
                    'message': 'Message retried successfully',
                    'data': self.get_serializer(new_message).data
                })
            except Exception as e:
                message.update_status('error', str(e))
                return Response({
                    'status': 'error',
                    'message': 'Failed to regenerate response',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error retrying message: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to retry message',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChatView(BaseViewSet):
    permission_classes = [AllowAny]
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def create(self, request):
        try:
            message = request.data.get('message')
            conversation_id = request.data.get('conversation_id')
            
            if not message:
                return Response({
                    "status": "error",
                    "message": "Message is required",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            def event_stream():
                for chunk in process_message(message, conversation_id):
                    yield f"data: {json.dumps({
                        'content': chunk,
                        'status': 'success',
                        'type': 'message'
                    })}\n\n"
            
            response = StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reload_knowledge_base(self, request):
        try:
            load_knowledge_base(force=True)
            return Response({
                "status": "success",
                "message": "Knowledge base reloaded successfully",
                "data": None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Knowledge base reload error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Handle file uploads to the knowledge base."""
        try:
            files = request.FILES.getlist('files')
            if not files:
                return Response({
                    "status": "error",
                    "message": "No files provided",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            uploaded_files = []
            for file in files:
                # Validate file type
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext not in ['.pdf', '.docx', '.txt', '.csv', '.pptx', '.xlsx', '.html', '.md', '.rtf']:
                    continue

                # Save file to knowledge base directory
                file_path = os.path.join('knowledge_base', file.name)
                path = default_storage.save(file_path, ContentFile(file.read()))
                uploaded_files.append(path)

            if uploaded_files:
                # Reload knowledge base with new files
                load_knowledge_base(force=True)
                return Response({
                    "status": "success",
                    "message": f"Successfully uploaded {len(uploaded_files)} files",
                    "data": {
                    "files": uploaded_files
                    }
                })
            else:
                return Response({
                    "status": "error",
                    "message": "No valid files were uploaded",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
