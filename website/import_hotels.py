import django
import sys
import os
django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()
from sightseeing.models import Hotel, Destinations, Location

def clear_all_data():
    Hotel.objects.all().delete()
    Destinations.objects.all().delete()
    Location.objects.all().delete()
    print('All Hotel, Destinations, and Location data deleted.')

import csv
import os
import django
import sys

# Setup Django environment
django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Hotel, Location

CSV_PATH = os.path.join(django_project_path, 'hotels_data.csv')

def import_hotels():
    with open(CSV_PATH, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            location_name = row.get('Location')
            if location_name:
                norm_location = location_name.strip().title()
                try:
                    location_obj = Location.objects.get(locationName=norm_location)
                except Location.DoesNotExist:
                    print(f"[WARNING] Location '{norm_location}' không tồn tại, bỏ qua hotel '{row.get('name')}'")
                    continue
            else:
                location_obj = None
            hotel = Hotel(
                name=row.get('name'),
                location=location_obj,
                address=row.get('address'),
                rating=float(row.get('ratings', 0) or 0),
                price=row.get('price'),
                image_url=row.get('image_url'),
            )
            hotel.save()
    print('Hotels data imported successfully.')

if __name__ == '__main__':
    import_hotels()
