from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Conversation, Message
from .chatbot_serializers import ConversationSerializer, MessageSerializer
from .llm_integration import generate_response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.views import APIView
from .llm_integration import generate_response 

    
class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)  # Filter by current user
        
        # Handle recent parameter
        if self.request.query_params.get('recent'):
            queryset = queryset.order_by('-created_at')
            
        # Handle limit parameter
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
                
        return queryset

# Update the ConversationListView class
class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]  # Add this to ensure user is logged in
    
    def get(self, request):
        try:
            conversations = Conversation.objects.filter(
                user=request.user  # Make sure to filter by the current user
            ).order_by('-created_at')[:10]  # Get 10 most recent conversations
            
            if not conversations.exists():
                return Response([], status=status.HTTP_200_OK)  # Return empty array if no conversations
            
            serializer = ConversationSerializer(conversations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.filter(is_deleted=False)
    serializer_class = MessageSerializer

    def create(self, request):
        if not request.data.get('content'):
            return Response({"error": "Message content is required"}, status=400)
        try:
            # Get or create conversation
            conversation_id = request.data.get('conversation')
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id)
            else:
                first_message = request.data.get('content')[:30] + ("..." if len(request.data.get('content')) > 30 else "")
                conversation = Conversation.objects.create(
                    title=f"Chat: {first_message}",
                    user=request.user
                )

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
                'status': 'success',
                'conversation': ConversationSerializer(conversation).data,
                'messages': [
                    MessageSerializer(user_message).data,
                    MessageSerializer(ai_message).data
                ]
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # Inside MessageViewSet
    def partial_update(self, request, pk=None):
         message = self.get_object()
         message.content = request.data.get('content', message.content)
         message.save()
         return Response(MessageSerializer(message).data)

    def destroy(self, request, pk=None):
        message = self.get_object()
        message.is_deleted = True
        message.save()
    
    # Also soft-delete subsequent AI response if exists
        next_message = Message.objects.filter(
            conversation=message.conversation,
            timestamp__gt=message.timestamp,
            is_user=False
    ).first()
    
        if next_message:
            next_message.is_deleted = True
            next_message.save()
    
        return Response(status=status.HTTP_204_NO_CONTENT)
    def get_queryset(self):
        queryset = super().get_queryset()
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        return queryset
    