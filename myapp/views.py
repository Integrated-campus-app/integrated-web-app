from django.shortcuts import render
from .models import Task, Notice
from .serializers import TaskSerializer, NoticeSerializer
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth.models import User  # Import User model
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'tasks': reverse('task-list', request=request, format=format),
        'notices': reverse('notice-list', request=request, format=format),
        'register': reverse('register', request=request, format=format),
        'login': reverse('login', request=request, format=format),
    })
# View for user registration
User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()  # Use the custom user model
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to register
# View for user login (using SimpleJWT)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer

    def perform_create(self, serializer):
        """Send WebSocket event when a notice is created."""
        notice = serializer.save()
        self.send_notice_event("create", notice)

    def perform_update(self, serializer):
        """Send WebSocket event when a notice is updated."""
        notice = serializer.save()
        self.send_notice_event("update", notice)

    def perform_destroy(self, instance):
        """Send WebSocket event when a notice is deleted."""
        notice_data = NoticeSerializer(instance).data
        instance.delete()
        self.send_notice_event("delete", notice_data)

    def send_notice_event(self, action, notice):
        """Helper method to send WebSocket messages."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notice_board",
            {
                "type": "send_notice",
                "action": action,
                "notice": NoticeSerializer(notice).data,
            },
        )
