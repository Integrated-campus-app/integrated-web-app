from rest_framework import generics, status
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import PublicEndpoint
from django.utils import timezone

class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [PublicEndpoint]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.filter(
            is_deleted=False
        ).order_by("-updated_at")[:10]

class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [PublicEndpoint]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.filter(is_deleted=False)
        
    def perform_destroy(self, instance):
        instance.delete()  # Uses the model's soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [PublicEndpoint]

    def get_queryset(self):
        return Message.objects.filter(
            conversation_id=self.kwargs['conversation_id'],
            is_deleted=False
        ).order_by('created_at')

class MessageUpdateView(generics.UpdateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [PublicEndpoint]
    lookup_field = 'id'

    def get_queryset(self):
        return Message.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        serializer.save(edited_at=timezone.now())

class MessageDeleteView(generics.DestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [PublicEndpoint]
    lookup_field = 'id'

    def get_queryset(self):
        return Message.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.delete()  # Uses the model's soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)