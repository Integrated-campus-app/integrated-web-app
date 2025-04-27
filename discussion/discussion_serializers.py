from rest_framework import serializers
from .models import Question, Answer, Tag, QuestionVote, AnswerVote
from .models import QuestionVote, AnswerVote

class QuestionVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionVote
        fields = ['id', 'user', 'question', 'vote']
        read_only_fields = ['user']

class AnswerVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerVote
        fields = ['id', 'user', 'answer', 'vote']
        read_only_fields = ['user']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class QuestionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    answers_count = serializers.IntegerField(read_only=True)
    question_user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'user', 'question_user_id', 'title', 'content',
            'tags', 'created_at', 'views', 'answers_count', 'is_closed'
        ]

    def get_user(self, obj):
        return obj.user.username if obj.user else "Anonymous"

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_question_user_id(self, obj):
        return obj.user.id if obj.user else None
    
    def get_answers_count(self, obj):
        return obj.answers.count()

class AnswerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    weighted_score = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField(read_only=True)
    question_id = serializers.IntegerField(source='question.id', read_only=True)

    class Meta:
        model = Answer
        fields = ['id', 'question_id', 'user', 'content', 'created_at', 'weighted_score', 'user_vote']
        extra_kwargs = {
            'content': {'required': True},
            'question': {'write_only': True},
        }

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.answervote_set.filter(user=request.user).first()
            return vote.vote if vote else 0
        return None

    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Answer must be at least 10 characters.")
        return value

