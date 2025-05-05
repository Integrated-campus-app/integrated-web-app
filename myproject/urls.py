from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('authentication.urls')),  # For authenticated features
    path('api/', include('chatbot.urls')),
    path('map/', include('location.urls')), 
    path('forum/', include('forum.urls')),
]