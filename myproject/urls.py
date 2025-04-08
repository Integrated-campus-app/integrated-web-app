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
    path('admin/', admin.site.urls),  # Django admin
    path('api/', api_root),  # Custom API root view
    path('api/', include(router.urls)),  # Include router URLs
    path('api/auth/', include('authentication.urls')), 
    # path("api/", include("myapp.urls")),  # Your existing API routes
    path('api/register/', UserRegistrationView.as_view(), name='register'),  # User registration
    path('api/login/', TokenObtainPairView.as_view(), name='login'),  # JWT login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWT refresh
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # OpenAPI schema
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger UI
]