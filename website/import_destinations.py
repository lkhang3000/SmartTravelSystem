"""
Script to import destinations from CSV file to database
Run this script: python manage.py shell < import_destinations.py
Or: python import_destinations.py (if DJANGO_SETTINGS_MODULE is set)
"""

import os
import sys
import django
import csv

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations

def get_region_from_location(location):
    """Use location name directly as region"""
    return location.strip()

def get_default_image_url(category, location):
    """Get default image URL based on category and location"""
    
    # Map categories to default images
    image_map = {
        'Museums': '/static/images/museum-default.jpg',
        'Landmarks': '/static/images/landmark-default.jpg',
        'Shrines/Temples': '/static/images/temple-default.jpg',
        'Beaches': '/static/images/beach-default.jpg',
    }
    
    # Return category-based image or general default
    return image_map.get(category, '/static/images/destination-default.jpg')

def import_destinations(csv_file_path):
    """Import destinations from CSV file"""
    
    print(f"Starting import from {csv_file_path}...")
    
    # Track statistics
    total_rows = 0
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    file_content = None
    
    for encoding in encodings:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as file:
                file_content = file.read()
            break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        print("❌ Could not read CSV file with any encoding")
        return
    
    # Parse CSV
    from io import StringIO
    csv_file = StringIO(file_content)
    reader = csv.DictReader(csv_file)
    
    with open(csv_file_path, 'r', encoding=encoding) as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            total_rows += 1
            
            try:
                name = row['name'].strip()
                address = row['address'].strip()
                rating = float(row['ratings'])
                category = row['category'].strip()
                description = row['description'].strip()
                location = row['location'].strip()
                
                # Get or create location
                location_obj, _ = Location.objects.get_or_create(locationName=location)
                
                # Check if destination already exists
                destination, created = Destinations.objects.update_or_create(
                    desName=name,
                    defaults={
                        'location': location_obj,
                        'address': address,
                        'description': description,
                        'category': category,
                        'rating': rating,
                        'image_url': get_default_image_url(category, location),
                        'price_range': 'Free - Moderate',  # Default value
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"✅ Created: {name} ({location})")
                else:
                    updated_count += 1
                    print(f"🔄 Updated: {name} ({location})")
                    
            except Exception as e:
                skipped_count += 1
                print(f"❌ Error processing row {total_rows}: {e}")
                continue
    
    # Print summary
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Total rows processed: {total_rows}")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (errors): {skipped_count}")
    print("="*50)
    
    # Show location statistics
    print("\nLOCATION STATISTICS:")
    for location in Location.objects.all():
        count = Destinations.objects.filter(location=location).count()
        print(f"  {location.locationName}: {count} destinations")

if __name__ == '__main__':
    csv_file = os.path.join(os.path.dirname(__file__), 'data.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file not found at {csv_file}")
        sys.exit(1)
    
    # Confirm before import
    print(f"This will import destinations from: {csv_file}")
    print(f"Existing destinations with the same name will be updated.")
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        import_destinations(csv_file)
    else:
        print("Import cancelled.")
