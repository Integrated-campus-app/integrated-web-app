from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = (
            "id", 
            "created_at", 
            "conversation", 
            "is_user",
            "is_deleted",
            "deleted_at"
        )

    def validate(self, data):
        """Prevent editing non-user messages"""
        if self.instance and not self.instance.is_user:
            raise serializers.ValidationError("Cannot edit bot messages")
        return data

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = "__all__"
        read_only_fields = (
            "created_at", 
            "updated_at",
            "is_deleted",
            "deleted_at"
        )