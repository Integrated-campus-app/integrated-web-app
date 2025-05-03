from django.urls import re_path
from discussion.consumers import MyWebSocketConsumer, NoticeConsumer, ChatConsumer, NoticeBoardConsumer
from django.urls import path
from chatbot.consumers import ChatbotConsumer
from . import consumers
websocket_urlpatterns = [
    re_path(r'ws/questions/(?P<question_id>\d+)/$', consumers.QuestionConsumer.as_asgi()),
    path("ws/chat/", ChatbotConsumer.as_asgi()),
    
]
