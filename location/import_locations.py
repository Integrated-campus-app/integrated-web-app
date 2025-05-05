import json
from django.core.management.base import BaseCommand
from .models import LocationCategory, Location

class Command(BaseCommand):
    help = 'Import initial location data from JSON'
    
    def handle(self, *args, **options):
        # Load your JSON data
        with open('locations_data.json') as f:
            data = json.load(f)
        
        # Create categories first
        categories = {}
        for item in data['features']:
            cat_name = item['properties']['category'].lower()
            if cat_name not in categories:
                # Map to appropriate FontAwesome icon
                icon_map = {
                    'entrance': 'fa-door-open',
                    'cafe': 'fa-coffee',
                    'school': 'fa-school',
                    'department': 'fa-user-tie',
                    'lab': 'fa-flask',
                    'court': 'fa-basketball',
                    'stadium': 'fa-running',
                    'amphi': 'fa-microphone',
                    'classroom': 'fa-school',
                    'stem': 'fa-flask',
                    'lounge': 'fa-home',
                    'library': 'fa-book'
                }
                category, _ = LocationCategory.objects.get_or_create(
                    name=cat_name.capitalize(),
                    defaults={'icon_class': icon_map.get(cat_name, 'fa-map-marker')}
                )
                categories[cat_name] = category
        
        # Create locations
        for item in data['features']:
            Location.objects.create(
                name=item['properties']['name'],
                category=categories[item['properties']['category'].lower()],
                coordinates=item['geometry']['coordinates'],
                description=item['properties'].get('description', '')
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully imported locations'))