from rest_framework import generics, permissions
from .models import Location, LocationCategory, UserFavoriteLocation
from .location_serializers import LocationSerializer, LocationCategorySerializer, UserFavoriteLocationSerializer

class LocationList(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]  # Public access

class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]  # Public access

class LocationCategoryList(generics.ListAPIView):
    queryset = LocationCategory.objects.all()
    serializer_class = LocationCategorySerializer
    permission_classes = [permissions.AllowAny]  # Public access

class UserFavoriteLocationList(generics.ListCreateAPIView):
    serializer_class = UserFavoriteLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserFavoriteLocation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserFavoriteLocationDetail(generics.RetrieveDestroyAPIView):
    serializer_class = UserFavoriteLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserFavoriteLocation.objects.filter(user=self.request.user)