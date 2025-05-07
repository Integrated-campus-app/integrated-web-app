from django.contrib import admin
from .models import Building, Location

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'building', 'latitude', 'longitude')  # Changed 'type' to 'category'
    list_filter = ('category', 'building')  # Changed 'type' to 'category'
    search_fields = ('name', 'description')