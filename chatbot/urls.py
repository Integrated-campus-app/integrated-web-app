from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .chatbot_views import ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet)  # Will be at /api/conversations/
router.register(r'messages', MessageViewSet)           # Will be at /api/messages/

urlpatterns = [
    path('', include(router.urls)),
]