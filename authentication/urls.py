from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    NoticeListView,
    NoticeDetailView,
    RegisterView,
    CustomTokenObtainPairView,
    FeedbackCreateView,
    IssueReportCreateView,
    IssueReportListView,
    NotificationTestView,
    LocationCategoryListView,
    CampusLocationListView,
    CampusLocationDetailView,
    UserFavoriteLocationView,
    RemoveFavoriteView, QuestionListView, QuestionDetailView,
    AnswerCreateView, AnswerDetailView, AnswerListView,
    TagListView, QuestionVoteView,
    AnswerVoteView
)

urlpatterns = [
    # Remove 'api/' prefix since it's already included in the main urls.py
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('notifications/test/', NotificationTestView.as_view(), name='test-notify'),
    path('feedback/', FeedbackCreateView.as_view(), name='feedback'),
    path('issues/', IssueReportCreateView.as_view(), name='report-issue'),
    path('admin/issues/', IssueReportListView.as_view(), name='issue-list'),
    path('notices/', NoticeListView.as_view(), name='notice-list'),
    path('notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),
    path('map/categories/', LocationCategoryListView.as_view(), name='location-categories'),
    path('map/locations/', CampusLocationListView.as_view(), name='location-list'),
    path('map/locations/<int:pk>/', CampusLocationDetailView.as_view(), name='location-detail'),
    path('map/favorites/', UserFavoriteLocationView.as_view(), name='user-favorites'),
    path('map/favorites/<int:pk>/', RemoveFavoriteView.as_view(), name='remove-favorite'),
    # Discussion Forum Endpoints
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='question-detail'),
    path('questions/', QuestionListView.as_view(), name='question-list'),

    path('questions/<int:question_id>/answers/create/', AnswerCreateView.as_view(), name='answer-create'),
    path('questions/<int:question_id>/answers/', AnswerListView.as_view(), name='answer-list'),
    path('answers/<int:pk>/', AnswerDetailView.as_view(), name='answer-detail'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('questions/<int:question_id>/vote/', QuestionVoteView.as_view(), name='question-vote'),
    # urls.py
    path('answers/<int:answer_id>/vote/', AnswerVoteView.as_view(), name='answer-vote'),
]
# Note: The 'api/' prefix is already included in the main urls.py, so we don't need to repeat it here.
# This keeps the URLs clean and avoids redundancy.