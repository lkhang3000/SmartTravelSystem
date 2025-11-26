import csv
import os
import django
import sys

django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations, Location

CSV_PATH = os.path.join(django_project_path, 'data.csv')

def import_destinations():
    try:
        with open(CSV_PATH, encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                location_name = row.get('location')
                if location_name:
                    norm_location = location_name.strip().title()
                    location_obj, _ = Location.objects.get_or_create(locationName=norm_location)
                else:
                    location_obj = None
                dest = Destinations(
                    desName=row.get('name'),
                    location=location_obj,
                    description=row.get('description'),
                    price_range=None,
                    category=row.get('category'),
                    rating=float(row.get('ratings', 0) or 0),
                    address=row.get('address'),
                    image_url=None,
                )
                dest.save()
        print('Destinations data imported successfully.')
    except UnicodeDecodeError:
        with open(CSV_PATH, encoding='latin1') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                location_name = row.get('location')
                if location_name:
                    norm_location = location_name.strip().title()
                    location_obj, _ = Location.objects.get_or_create(locationName=norm_location)
                else:
                    location_obj = None
                dest = Destinations(
                    desName=row.get('name'),
                    location=location_obj,
                    description=row.get('description'),
                    price_range=None,
                    category=row.get('category'),
                    rating=float(row.get('ratings', 0) or 0),
                    address=row.get('address'),
                    image_url=None,
                )
                dest.save()
        print('Destinations data imported successfully (latin1 encoding).')

if __name__ == '__main__':
    import_destinations()
