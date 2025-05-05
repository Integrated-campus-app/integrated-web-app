from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    MessageListView,
    MessageUpdateView,
    MessageDeleteView,
    
)
from .sse import chat_stream
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health_check),
    
    # Conversation endpoints
    path("conversations/", ConversationListCreateView.as_view(), name="conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    
    # Message endpoints
    path("messages/<int:id>/", MessageUpdateView.as_view(), name="message-update"),
    path("messages/<int:id>/delete/", MessageDeleteView.as_view(), name="message-delete"),
    path("conversations/<int:conversation_id>/messages/", 
        MessageListView.as_view(), 
        name="message-list"),
    
    # Chat streaming
    path("chat/stream/", chat_stream, name="chat-stream"),
]