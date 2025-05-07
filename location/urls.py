# urls.py
from django.urls import path
from .views import LocationListView, LocationSearchView, NavigationView

urlpatterns = [
    path('locations/', LocationListView.as_view(), name='location-list'),
    path('locations/search/', LocationSearchView.as_view(), name='location-search'),
    path('navigation/', NavigationView.as_view(), name='navigation'),
]
