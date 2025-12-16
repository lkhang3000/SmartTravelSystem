import os
import sys
import django

# Add the website directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'website'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location

# Delete invalid locations
invalid_locations = ['4.3', 'Location']
deleted_count = Location.objects.filter(locationName__in=invalid_locations).delete()[0]

print(f"✓ Deleted {deleted_count} invalid locations")

# Show remaining locations
remaining = Location.objects.all().order_by('locationName')
print(f"\nRemaining locations ({remaining.count()}):")
for loc in remaining:
    print(f"  - {loc.locationName}")
