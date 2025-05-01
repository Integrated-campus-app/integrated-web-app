from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Conversation, Message
from .chatbot_serializers import ConversationSerializer, MessageSerializer
from .llm_integration import generate_response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import AllowAny

    
class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    throttle_classes = [AnonRateThrottle]
    permission_classes = [AllowAny] 

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.filter(is_deleted=False)
    serializer_class = MessageSerializer
    permission_classes = [AllowAny] 

    def create(self, request):
        # Create a new conversation if none exists
        conversation = Conversation.objects.create(title="New Chat")
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=request.data.get('content'),
            is_user=True
        )
        
        # Generate AI response
        ai_response = generate_response(request.data.get('content'))
        
        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            content=ai_response,
            is_user=False
        )
        
        return Response({
            'user_message': MessageSerializer(user_message).data,
            'ai_message': MessageSerializer(ai_message).data,
            'conversation_id': conversation.id  # For frontend tracking
        })
        # Inside MessageViewSet
    def partial_update(self, request, pk=None):
         message = self.get_object()
         message.content = request.data.get('content', message.content)
         message.save()
         return Response(MessageSerializer(message).data)

    def destroy(self, request, pk=None):
         message = self.get_object()
         message.is_deleted = True  # Soft delete
         message.save()
         return Response(status=status.HTTP_204_NO_CONTENT)