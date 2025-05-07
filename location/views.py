# views.py
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

from myproject import settings
from .models import Location
from .serializers import LocationSerializer
from rest_framework import generics, permissions

# List all locations (filterable by type/building)
class LocationListView(generics.ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Location.objects.all()
        # Filter by category (e.g., ?category=LAB)
        if category := self.request.query_params.get('category'):
            queryset = queryset.filter(category=category)
        # Filter by building (e.g., ?building=1)
        if building_id := self.request.query_params.get('building'):
            queryset = queryset.filter(building_id=building_id)
        return queryset

# Search locations by name/description
class LocationSearchView(generics.ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        return Location.objects.filter(name__icontains=query)

# Get navigation route (using Mapbox Directions API)
class NavigationView(APIView):
    permission_classes = [permissions.AllowAny]  # Added this line to make it public
    
    def get(self, request):
        required_params = ['from_lat', 'from_lng', 'to_lat', 'to_lng']
        if any(param not in request.query_params for param in required_params):
            return Response({'error': 'Missing coordinates'}, status=400)
        
        try:
            from_lat = float(request.query_params['from_lat'])
            from_lng = float(request.query_params['from_lng'])
            to_lat = float(request.query_params['to_lat'])
            to_lng = float(request.query_params['to_lng'])
            mode = request.query_params.get('mode', 'walking')  # Add transport mode
        except ValueError:
            return Response({'error': 'Invalid coordinates'}, status=400)

        mapbox_token = settings.MAPBOX_TOKEN  # Move to Django settings
        profile = {
            'walking': 'walking',
            'cycling': 'cycling',
            'driving': 'driving'
        }.get(mode, 'walking')

        url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{from_lng},{from_lat};{to_lng},{to_lat}"
        params = {
            'access_token': mapbox_token,
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return Response(response.json())
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=500)