from django.urls import path, include

urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('discussion/', include('discussion.urls')),
    path('map/', include('location.urls')),
    
    # Optional: API docs or admin URLs
    # path('admin/', admin.site.urls),
]