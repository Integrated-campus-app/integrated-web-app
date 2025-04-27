from rest_framework import generics, permissions
from .models import LocationCategory, CampusLocation, UserFavoriteLocation
from .location_serializers import (
    LocationCategorySerializer,
    CampusLocationSerializer,
    UserFavoriteLocationSerializer
)

class LocationCategoryListView(generics.ListAPIView):
    queryset = LocationCategory.objects.all()
    serializer_class = LocationCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CampusLocationListView(generics.ListAPIView):
    queryset = CampusLocation.objects.all()
    serializer_class = CampusLocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CampusLocationDetailView(generics.RetrieveAPIView):
    queryset = CampusLocation.objects.all()
    serializer_class = CampusLocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserFavoriteLocationView(generics.ListCreateAPIView):
    serializer_class = UserFavoriteLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFavoriteLocation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RemoveFavoriteView(generics.DestroyAPIView):
    queryset = UserFavoriteLocation.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)