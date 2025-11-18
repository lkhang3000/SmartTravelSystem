import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations

print(f'Total Locations: {Location.objects.count()}')
print('\nLocations:')
for loc in Location.objects.all().order_by('locationName'):
    print(f'  - {loc.locationName} (ID: {loc.id})')

print(f'\nTotal Categories: {Destinations.objects.values_list("category", flat=True).distinct().count()}')
print('\nCategories:')
categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
for cat in categories:
    if cat:
        print(f'  - {cat}')
