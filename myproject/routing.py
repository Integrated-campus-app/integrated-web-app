from django.urls import re_path
from discussion.consumers import MyWebSocketConsumer, NoticeConsumer, ChatConsumer, NoticeBoardConsumer
from . import consumers
websocket_urlpatterns = [
    re_path(r'ws/questions/(?P<question_id>\d+)/$', consumers.QuestionConsumer.as_asgi()),

    
]
