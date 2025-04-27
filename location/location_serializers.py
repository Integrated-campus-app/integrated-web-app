from rest_framework import serializers
from .models import LocationCategory, CampusLocation, UserFavoriteLocation



class LocationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationCategory
        fields = ['id', 'name', 'icon_class']

class CampusLocationSerializer(serializers.ModelSerializer):
    category = LocationCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=LocationCategory.objects.all(),
        source='category',
        write_only=True,
        required=True
    )
    class Meta:
        model = CampusLocation
        fields = [
            'id', 'name', 'description', 'longitude', 'latitude',
            'category', 'category_id', 'department', 'department_id',
            'floor_level', 'is_accessible', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class UserFavoriteLocationSerializer(serializers.ModelSerializer):
    location = CampusLocationSerializer(read_only=True)
    
    class Meta:
        model = UserFavoriteLocation
        fields = ['id', 'location', 'created_at']