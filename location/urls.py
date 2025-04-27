from django.urls import path
from .views import (
    LocationCategoryListView,
    CampusLocationListView,
    CampusLocationDetailView,
    UserFavoriteLocationView,
    RemoveFavoriteView
)

urlpatterns = [
    path('categories/', LocationCategoryListView.as_view(), name='location-categories'),
    path('locations/', CampusLocationListView.as_view(), name='location-list'),
    path('locations/<int:pk>/', CampusLocationDetailView.as_view(), name='location-detail'),
    path('favorites/', UserFavoriteLocationView.as_view(), name='user-favorites'),
    path('favorites/<int:pk>/', RemoveFavoriteView.as_view(), name='remove-favorite'),
]