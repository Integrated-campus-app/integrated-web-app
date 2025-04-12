from django.urls import re_path
from myapp.consumers import MyWebSocketConsumer, NoticeConsumer, ChatConsumer, NoticeBoardConsumer

websocket_urlpatterns = [
    re_path(r'ws/socket-server/', MyWebSocketConsumer.as_asgi()),
    re_path(r'ws/notices/', NoticeConsumer.as_asgi()),
    re_path(r"ws/chat/", ChatConsumer.as_asgi()),
    re_path(r"ws/notice-board/$", NoticeBoardConsumer.as_asgi()),
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),  # New
    
]
