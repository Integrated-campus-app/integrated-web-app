from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.db import models
from .models import (
    Question, Answer, Tag, 
    QuestionVote, AnswerVote
)
from django.db.models import Count, Sum 
from .models import LocationCategory, Task, Notice, Message, Feedback, IssueReport, CustomUser, Department, CampusLocation, UserFavoriteLocation
# =====================User Map MODEL=====================
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']
# ================= AUTHENTICATION SERIALIZERS =================
User = get_user_model()
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'university_email', 'password', 'password2']
        extra_kwargs = {
            'university_email': {'required': True},
            'username': {
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message="This username is already taken"
                    )
                ]
            }
        }

    def validate_university_email(self, value):
        if not value.endswith('@astu.edu.et'):
            raise serializers.ValidationError("Only @astu.edu.et emails allowed")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            university_email=validated_data['university_email'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Allow login with either username or email
        username = attrs.get('username')
        if '@' in username:  # If input looks like email
            try:
                user = User.objects.get(university_email=username)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass
        
        data = super().validate(attrs)
        
        # Add user data to response
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.university_email,
                'is_admin': self.user.is_admin
            }
        })
        return data
    
    #=================LOCATION SERIALIZERS=================
    # serializers.py
class LocationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationCategory
        fields = ['id', 'name', 'icon_class']

class CampusLocationSerializer(serializers.ModelSerializer):
    category = LocationCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=LocationCategory.objects.all(),
        source='category',
        write_only=True,
        required=True  # Category remains required
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,  # Make department optional
        allow_null=True  # Explicitly allow null
    )
    
    class Meta:
        model = CampusLocation
        fields = [
            'id', 'name', 'description', 
            'longitude', 'latitude', 'category',
            'category_id', 'department', 'department_id',
            'floor_level', 'is_accessible', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class UserFavoriteLocationSerializer(serializers.ModelSerializer):
    location = CampusLocationSerializer(read_only=True)
    
    class Meta:
        model = UserFavoriteLocation
        fields = ['id', 'location', 'created_at']
# ================= APPLICATION SERIALIZERS =================

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']

class NoticeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Notice
        fields = [
            'id',
            'title',
            'content',
            'department',
            'department_id',
            'priority',
            'created_by',
            'created_at',
            'updated_at',
            'expiration_date',
            'is_pinned'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
 

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    receiver = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'receiver',
            'content',
            'timestamp',
            'is_read'
        ]
        read_only_fields = ['sender', 'timestamp']

class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id',
            'user',
            'feedback_type',
            'content',
            'is_anonymous',
            'created_at',
            'response'
        ]
        read_only_fields = ['user', 'created_at', 'response']

class IssueReportSerializer(serializers.ModelSerializer):
    reporter = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.SlugRelatedField(
        slug_field='username',
        queryset=CustomUser.objects.filter(is_admin=True),
        required=False
    )

    class Meta:
        model = IssueReport
        fields = [
            'id',
            'reporter',
            'title',
            'description',
            'category',
            'status',
            'assigned_to',
            'created_at',
            'resolved_at'
        ]
        read_only_fields = ['reporter', 'created_at']

        #=================Group discussion SERIALIZERS=================
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class QuestionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    tags = TagSerializer(many=True, read_only=True)
    answers_count = serializers.SerializerMethodField()
    views = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'user', 'title', 'content', 
            'tags', 'created_at', 'updated_at',
            'views', 'answers_count', 'is_closed'
        ]
    
    def get_answers_count(self, obj):
        return obj.answers.count()

class AnswerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    vote_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'id', 'user', 'question', 'content',
            'created_at', 'updated_at', 'is_accepted',
            'vote_count'
        ]
        extra_kwargs = {
            'question': {'write_only': True}
        }
    
    def get_vote_count(self, obj):
        return obj.answervote_set.aggregate(
            total_votes=models.Sum('vote')
        )['total_votes'] or 0

class QuestionVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionVote
        fields = ['id', 'user', 'question', 'vote']
        extra_kwargs = {
            'user': {'read_only': True},
            'question': {'write_only': True}
        }

class AnswerVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerVote
        fields = ['id', 'user', 'answer', 'vote']
        extra_kwargs = {
            'user': {'read_only': True},
            'answer': {'write_only': True}
        }