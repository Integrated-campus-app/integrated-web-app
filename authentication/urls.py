from django.urls import path
from .views import NoticeListView, NoticeDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    FeedbackCreateView,
    IssueReportCreateView,
    IssueReportListView,
    NotificationTestView  # Add this
)

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/notifications/test/', NotificationTestView.as_view(), name='test-notify'),  # Fixed
    path('api/feedback/', FeedbackCreateView.as_view(), name='feedback'),
    path('api/issues/', IssueReportCreateView.as_view(), name='report-issue'),
    path('api/admin/issues/', IssueReportListView.as_view(), name='issue-list'),
    path('api/notices/', NoticeListView.as_view(), name='notice-list'),
    path('api/notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),
]