from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .llm_integration import stream_response, RATE_LIMIT, RATE_LIMIT_WINDOW
import json
import logging

logger = logging.getLogger(__name__)

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        try:
            logger.info("Attempting to fetch conversations...")
            queryset = Conversation.objects.filter(
                is_deleted=False
            ).order_by('-updated_at')
            count = queryset.count()
            logger.info(f"Successfully fetched {count} conversations")
            return queryset
        except Exception as e:
            logger.error(f"Error fetching conversations: {str(e)}", exc_info=True)
            # Return empty queryset instead of Response to avoid double response
            return Conversation.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in list view: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch conversations", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        try:
            conversation = serializer.save()
            logger.info(f"Successfully created conversation with ID: {conversation.id}")
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
            raise

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            conversation = self.get_object()
            messages = Message.objects.filter(
                conversation=conversation,
                is_deleted=False
            ).order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            logger.info(f"Successfully fetched {messages.count()} messages for conversation {pk}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch messages", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            conversation = self.get_object()
            conversation.is_deleted = True
            conversation.deleted_at = timezone.now()
            conversation.save()
            logger.info(f"Successfully soft-deleted conversation {conversation.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to delete conversation", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(
            is_deleted=False
        ).order_by('created_at')

    def create(self, request, *args, **kwargs):
        try:
            # Check rate limit
            key = f"rate_limit_anonymous"
            count = cache.get(key, 0)
            
            if count >= RATE_LIMIT:
                return Response(
                    {"error": "Rate limit exceeded. Please wait a moment."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Validate conversation
            conversation_id = request.data.get('conversation')
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    is_deleted=False
                )
            except Conversation.DoesNotExist:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create message
            message = Message.objects.create(
                conversation=conversation,
                content=request.data.get('content'),
                is_user=True
            )

            # Update rate limit
            cache.set(key, count + 1, timeout=RATE_LIMIT_WINDOW)

            # Start SSE stream
            return StreamingHttpResponse(
                stream_response(request.data.get('content'), conversation),
                content_type='text/event-stream'
            )

        except Exception as e:
            logger.error(f"Error creating message: {e}", exc_info=True)
            return Response(
                {"error": "Failed to create message"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            message = self.get_object()
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            return Response(
                {"error": "Failed to delete message"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class NotificationStreamView(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        try:
            # Check rate limit
            key = f"rate_limit_anonymous"
            count = cache.get(key, 0)
            
            if count >= RATE_LIMIT:
                return Response(
                    {"error": "Rate limit exceeded. Please wait a moment."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Update rate limit
            cache.set(key, count + 1, timeout=RATE_LIMIT_WINDOW)

            # Start SSE stream
            return StreamingHttpResponse(
                stream_response(request.data.get('content')),
                content_type='text/event-stream'
            )

        except Exception as e:
            logger.error(f"Error in notification stream: {e}", exc_info=True)
            return Response(
                {"error": "Failed to establish stream"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
