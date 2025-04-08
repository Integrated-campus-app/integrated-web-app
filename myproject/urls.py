from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import TaskViewSet, NoticeViewSet, api_root, UserRegistrationView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'notices', NoticeViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Endpoints
    path('api/', api_root),
    path('api/', include(router.urls)),
    
    # Authentication Endpoints (grouped under api/auth/)
    path('api/auth/', include([
        path('register/', UserRegistrationView.as_view(), name='register'),
        path('login/', TokenObtainPairView.as_view(), name='login'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    ])),
]