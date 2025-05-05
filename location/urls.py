from django.urls import path
from . import location_views

urlpatterns = [
    path('locations/', location_views.LocationList.as_view(), name='location-list'),
    path('locations/<int:pk>/', location_views.LocationDetail.as_view(), name='location-detail'),
    path('categories/', location_views.LocationCategoryList.as_view(), name='category-list'),
    path('favorites/', location_views.UserFavoriteLocationList.as_view(), name='favorite-list'),
    path('favorites/<int:pk>/', location_views.UserFavoriteLocationDetail.as_view(), name='favorite-detail'),
]