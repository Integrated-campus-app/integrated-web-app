from django.urls import path
from django.views.decorators.http import require_http_methods
from . import sse

urlpatterns = [
    path('sse/chat/', require_http_methods(["GET", "OPTIONS"])(sse.chat_stream), name='chat-sse'),
]
