from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .chatbot_views import ConversationViewSet, MessageViewSet
from .chatbot_views import ConversationListView
from rest_framework.routers import DefaultRouter
from . import sse

router = DefaultRouter()
router.register(r'chat/conversations', ConversationViewSet)
router.register(r'chat/messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('sse/chat/', sse.chat_stream, name='chat-sse'),
    # path('chat/conversations/recent/', ConversationListView.as_view(), name='recent-conversations'),
    
]