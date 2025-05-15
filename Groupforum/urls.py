from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from .views import *
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})

router = DefaultRouter()
router.register(r'questions', views.QuestionViewSet)
router.register(r'answers', views.AnswerViewSet)
router.register(r'comments', views.CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),  # All forum API endpoints
    path('csrf/', get_csrf, name='get_csrf'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/stream/', views.NotificationStreamView.as_view(), name='notification-stream'),
]