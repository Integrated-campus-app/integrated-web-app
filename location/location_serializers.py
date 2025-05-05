from rest_framework import serializers
from .models import Location, LocationCategory, UserFavoriteLocation

class LocationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationCategory
        fields = ['id', 'name', 'icon_class']

class LocationSerializer(serializers.ModelSerializer):
    category = LocationCategorySerializer(read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'category', 'description', 'coordinates', 'is_common']

class UserFavoriteLocationSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = UserFavoriteLocation
        fields = ['id', 'user', 'location', 'created_at']
        read_only_fields = ['user', 'created_at']