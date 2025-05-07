import json
from django.core.management.base import BaseCommand
from django.db import transaction
from location.models import Location, Building

class Command(BaseCommand):
    help = 'Import locations from GeoJSON file'

    def handle(self, *args, **options):
        with open('location.geojson') as f:
            data = json.load(f)
            
            with transaction.atomic():
                for feature in data['features']:
                    self.create_location(feature)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {Location.objects.count()} locations'))

    def create_location(self, feature):
        # Normalize category to match model choices
        category_mapping = {
            'Entrance': 'ENTRANCE',
            'Lounge': 'LOUNGE',
            'Cafe': 'CAFE',
            'Court': 'COURT',
            'Stadium': 'STADIUM',
            'Amphi': 'AMPHI',
            'School': 'SCHOOL',
            'Department': 'DEPARTMENT',
            'Lab': 'LAB',
            'stem': 'STEM',
            'classroom': 'CLASSROOM',
            'Classroom': 'CLASSROOM'
        }
        
        raw_category = feature['properties']['category']
        normalized_category = category_mapping.get(raw_category, 'CLASSROOM')  # Default to classroom
        
        # Handle duplicate coordinates/names
        if Location.objects.filter(
            latitude=feature['geometry']['coordinates'][1],
            longitude=feature['geometry']['coordinates'][0],
            name=feature['properties']['name']
        ).exists():
            return
        
        Location.objects.create(
            name=feature['properties']['name'],
            category=normalized_category,
            latitude=feature['geometry']['coordinates'][1],  # GeoJSON uses [lng, lat]
            longitude=feature['geometry']['coordinates'][0],
            description=f"Imported from GeoJSON - Original category: {raw_category}"
        )