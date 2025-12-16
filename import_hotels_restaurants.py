import os
import sys
import django
import csv
from datetime import datetime

# Add the website directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'website'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Hotel, Restaurant, Location

def clear_old_hotels():
    """Delete all existing hotel data"""
    count = Hotel.objects.count()
    Hotel.objects.all().delete()
    print(f"✓ Deleted {count} old hotels")

def import_hotels_restaurants():
    """Import hotels and restaurants from CSV file"""
    csv_file = 'hotels.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    hotels_count = 0
    restaurants_count = 0
    errors = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Get or create location
                location_name = row['Location'].strip()
                location, _ = Location.objects.get_or_create(locationName=location_name)
                
                # Parse data
                name = row['Name'].strip()
                type_field = row['Type'].strip()
                address = row['Address'].strip()
                rating = float(row['Ratings']) if row['Ratings'] else 0.0
                price = int(row['Price']) if row['Price'] else 0
                image_url = row['Image'].strip() if row['Image'] else ''
                
                if type_field == 'Hotel':
                    # Create Hotel
                    hotel = Hotel.objects.create(
                        name=name,
                        location=location,
                        address=address,
                        rating=rating,
                        price=price,
                        image_url=image_url
                    )
                    hotels_count += 1
                    
                    if hotels_count % 50 == 0:
                        print(f"Imported {hotels_count} hotels...")
                
                elif type_field == 'Restaurant':
                    # Create Restaurant
                    restaurant = Restaurant.objects.create(
                        name=name,
                        location=location,
                        address=address,
                        rating=rating,
                        price=price,
                        image_url=image_url
                    )
                    restaurants_count += 1
                    
                    if restaurants_count % 50 == 0:
                        print(f"Imported {restaurants_count} restaurants...")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)} - {row.get('Name', 'Unknown')}"
                errors.append(error_msg)
                print(f"Error: {error_msg}")
    
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"✓ Hotels imported: {hotels_count}")
    print(f"✓ Restaurants imported: {restaurants_count}")
    print(f"✓ Total records: {hotels_count + restaurants_count}")
    
    if errors:
        print(f"\n⚠ Errors encountered: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
    else:
        print("\n✓ All records imported successfully!")

if __name__ == '__main__':
    print("Starting import process...")
    print("\nStep 1: Clearing old hotel data...")
    clear_old_hotels()
    
    print("\nStep 2: Importing hotels and restaurants...")
    import_hotels_restaurants()
    
    print("\n✓ Import completed!")
