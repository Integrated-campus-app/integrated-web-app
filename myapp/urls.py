from django.urls import path, include
from .views import api_root, TaskViewSet, NoticeViewSet
from rest_framework.routers import DefaultRouter
from myapp.views import UserRegistrationView
# Create a router and register viewsets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'notices', NoticeViewSet)

urlpatterns = [
    path('api/', api_root),  # Custom API root view
    path('api/', include(router.urls)),  # Include router URLs
    path('api/register/', UserRegistrationView.as_view(), name='register'),
]