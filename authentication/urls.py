from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .auth_views import RegisterView, CustomTokenObtainPairView, current_user

# urls.py
urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('current-user/', current_user, name='current-user'),
    path('register/', RegisterView.as_view(), name='register'),
]