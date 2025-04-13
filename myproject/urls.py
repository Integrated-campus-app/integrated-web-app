from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from authentication.views import (
    TaskListView,
    TaskDetailView,
    NoticeListView,
    NoticeDetailView,
    RegisterView,
    NotificationTestView,
    MessageCreateView,
    MessageListView,
    FeedbackCreateView,
    IssueReportCreateView,
    IssueReportListView,
    IssueReportUpdateView,
    QuestionListView
    
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Include authentication app URLs without duplicate 'api/' prefix
    path('api/', include('authentication.urls')),
    
    # Tasks Endpoints
    path('api/tasks/', TaskListView.as_view(), name='task-list'),
    path('api/tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    
    # Notices Endpoints
    path('api/notices/', NoticeListView.as_view(), name='notice-list'),
    path('api/notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),
    
    # Authentication Endpoints (moved to authentication/urls.py)
    
    # Notification Test
    path('api/notifications/test/', NotificationTestView.as_view(), name='notification-test'),
    
    # Messaging
    path('api/messages/', MessageCreateView.as_view(), name='message-create'),
    path('api/messages/list/', MessageListView.as_view(), name='message-list'),
    
    # Feedback
    path('api/feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
    
    # Issue Reports
    path('api/issues/', IssueReportCreateView.as_view(), name='issue-create'),
    path('api/issues/list/', IssueReportListView.as_view(), name='issue-list'),
    path('api/issues/<int:pk>/', IssueReportUpdateView.as_view(), name='issue-update'),
]