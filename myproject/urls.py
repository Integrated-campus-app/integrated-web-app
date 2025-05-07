from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),  # For authenticated features
    path('api/', include('chatbot.urls')),
    path('api/', include('location.urls')), 
    path('forum/', include('forum.urls')),
]