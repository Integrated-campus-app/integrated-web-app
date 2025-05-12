from rest_framework import serializers
from .models import *


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'is_read']
        read_only_fields = fields
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'text', 'created_at', 'anonymous_id', 'answer', 'parent_comment']
        extra_kwargs = {
            'answer': {'required': False},
            'parent_comment': {'required': False},
            'anonymous_id': {'required': False}
        }

    def validate(self, data):
        if not data.get('answer') and not data.get('parent_comment'):
            raise serializers.ValidationError(
                "A comment must be associated with either an answer or another comment"
            )
        return data  
    def create(self, validated_data):
        # Ensure anonymous_id is set
        if 'anonymous_id' not in validated_data or not validated_data['anonymous_id']:
            validated_data['anonymous_id'] = "anonymous_" + str(uuid.uuid4())[:8]
        return super().create(validated_data)    

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []