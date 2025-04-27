from rest_framework import serializers
from .models import Conversation, Message

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at']
        read_only_fields = ['created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'is_user', 'timestamp']
        read_only_fields = ['is_user', 'timestamp']