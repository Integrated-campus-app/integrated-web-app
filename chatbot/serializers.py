from rest_framework import serializers
from .models import Conversation, Message
from django.utils import timezone
from typing import Dict, Any

class MessageSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()
    edited_at = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    attachments = serializers.JSONField(required=False)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'content', 'is_user',
            'created_at', 'edited', 'edited_at', 'timestamp',
            'status', 'status_display', 'attachments',
            'source_hint', 'error_message'
        ]
        read_only_fields = [
            'id', 'created_at', 'edited', 'edited_at',
            'status', 'error_message'
        ]

    def get_timestamp(self, obj: Message) -> str:
        """Format timestamp for display."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

    def get_edited_at(self, obj: Message) -> str:
        """Format edited timestamp for display."""
        if obj.edited_at:
            return obj.edited_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_status_display(self, obj: Message) -> str:
        """Get human-readable status."""
        return dict(Message.STATUS_CHOICES).get(obj.status, obj.status)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate message data."""
        # Check if message is editable
        if self.instance and not self.instance.is_user:
            raise serializers.ValidationError("Cannot edit bot messages")

        # Validate content
        content = data.get('content', '').strip()
        if not content:
            raise serializers.ValidationError("Message content cannot be empty")

        # Validate attachments if present
        attachments = data.get('attachments', [])
        if attachments:
            from .utils import validate_attachment
            for attachment in attachments:
                if not validate_attachment(attachment):
                    raise serializers.ValidationError("Invalid attachment")

        # Set edited flag if content changed
        if self.instance and self.instance.content != content:
            data['edited'] = True
            data['edited_at'] = timezone.now()

        return data

    def to_representation(self, instance: Message) -> Dict[str, Any]:
        """Customize representation of message data."""
        data = super().to_representation(instance)
        
        # Format timestamps
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if instance.edited_at:
            data['edited_at'] = instance.edited_at.strftime('%Y-%m-%d %H:%M:%S')
            
        # Add status display
        data['status_display'] = dict(Message.STATUS_CHOICES).get(instance.status, instance.status)
        
        return data

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    deleted_at = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'deleted_at', 'is_deleted', 'is_archived',
            'messages', 'message_count', 'last_message'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'deleted_at',
            'is_deleted', 'is_archived'
        ]

    def get_message_count(self, obj: Conversation) -> int:
        """Get count of non-deleted messages."""
        return obj.messages.filter(is_deleted=False).count()

    def get_last_message(self, obj: Conversation) -> Dict[str, Any]:
        """Get the last message in the conversation."""
        last_message = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_created_at(self, obj: Conversation) -> str:
        """Format created timestamp."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

    def get_updated_at(self, obj: Conversation) -> str:
        """Format updated timestamp."""
        return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')

    def get_deleted_at(self, obj: Conversation) -> str:
        """Format deleted timestamp."""
        if obj.deleted_at:
            return obj.deleted_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def validate_title(self, value: str) -> str:
        """Validate conversation title."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()

    def to_representation(self, instance: Conversation) -> Dict[str, Any]:
        """Customize representation of conversation data."""
        data = super().to_representation(instance)
        
        # Format timestamps
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        if instance.deleted_at:
            data['deleted_at'] = instance.deleted_at.strftime('%Y-%m-%d %H:%M:%S')
            
        return data