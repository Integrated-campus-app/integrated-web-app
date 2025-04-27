from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .llm_integration import generate_response

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user
        ).order_by('timestamp')

    def create(self, request, *args, **kwargs):
        # Get or create a conversation
        conversation, created = Conversation.objects.get_or_create(
            user=request.user,
            defaults={'title': "New Chat"}
        )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=request.data.get('content'),
            is_user=True
        )
        
        # Get AI response
        ai_response = generate_response(request.data.get('content'))
        
        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            content=ai_response,
            is_user=False
        )
        
        return Response({
            'user_message': MessageSerializer(user_message).data,
            'ai_message': MessageSerializer(ai_message).data
        }, status=status.HTTP_201_CREATED)