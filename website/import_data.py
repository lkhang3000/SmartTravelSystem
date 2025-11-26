import os
import django
import csv

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations, Hotel

# Xóa dữ liệu Destinations
print("Deleting existing Destinations data...")
Destinations.objects.all().delete()

# Xóa dữ liệu Hotels
print("Deleting existing Hotels data...")
Hotel.objects.all().delete()

# Import từ data2.csv
print("Importing data from data2.csv...")
with open('d:\\SmartTravel\\data2.csv', 'r', encoding='utf-8-sig') as file:  # utf-8-sig to handle BOM
    reader = csv.DictReader(file)
    for row in reader:
        location_name = row['location'].strip()
        location, created = Location.objects.get_or_create(locationName=location_name)
        
        destination = Destinations(
            desName=row['name'].strip(),
            location=location,
            description=row['description'].strip() if row['description'] else None,
            category=row['category'].strip() if row['category'] else None,
            rating=float(row['ratings']) if row['ratings'] else 0.0,
            address=row['address'].strip() if row['address'] else None,
            image_url=row['image_url'].strip() if row['image_url'] else None,
        )
        try:
            destination.save()
        except Exception as e:
            print(f"Error saving destination {row['name']}: {e}")

print("Importing hotels from hotels_data.csv...")
with open('d:\\SmartTravel\\hotels_data.csv', 'r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        location_name = row['Location'].strip()
        location, created = Location.objects.get_or_create(locationName=location_name)
        
        hotel = Hotel(
            name=row['name'].strip(),
            location=location,
            address=row['address'].strip() if row['address'] else None,
            rating=float(row['ratings']) if row['ratings'] else 0.0,
            price=int(row['price']) if row['price'] else None,
            image_url=row['image_url'].strip() if row['image_url'] else None,
        )
        try:
            hotel.save()
        except Exception as e:
            print(f"Error saving hotel {row['name']}: {e}")

print("Data import completed!")