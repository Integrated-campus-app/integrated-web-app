# serializers.py
from rest_framework import serializers
from .models import Location, Building

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'name', 'latitude', 'longitude']

class LocationSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display')

    class Meta:
        model = Location
        fields = ['id', 'name', 'description', 'latitude', 'longitude', 'category', 'category_display', 'building']