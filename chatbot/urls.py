from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatView, ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'chat', ChatView, basename='chat')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]