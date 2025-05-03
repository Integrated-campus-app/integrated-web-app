from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('authentication.urls')),
    path('discussion/', include('discussion.urls')),
    path('map/', include('location.urls')), 
    path('api/', include('chatbot.urls')),
    # Optional: API docs or admin URLs
    # path('admin/', admin.site.urls),
]