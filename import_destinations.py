import os
import django
import csv
import sys
from datetime import datetime

# Add website folder to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'website'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations

def import_destinations_from_csv(csv_file_path):
    """Import destinations from CSV file"""
    
    print("Starting import process...")
    print(f"Reading from: {csv_file_path}")
    
    # Detect encoding
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    file_content = None
    used_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as f:
                file_content = f.read()
                used_encoding = encoding
                print(f"Successfully read file with encoding: {encoding}")
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        print("❌ Failed to read file with any encoding")
        return
    
    # Step 1: Clear old data
    print("\n1. Clearing old destination data...")
    old_count = Destinations.objects.count()
    Destinations.objects.all().delete()
    print(f"   Deleted {old_count} old destinations")
    
    # Step 2: Get or create locations and collect categories
    print("\n2. Processing locations and categories...")
    locations_set = set()
    categories_set = set()
    
    with open(csv_file_path, 'r', encoding=used_encoding) as file:
        csv_reader = csv.DictReader(file, delimiter=',')
        for row in csv_reader:
            if row.get('Location'):
                locations_set.add(row['Location'].strip().lower())
            if row.get('Type'):
                categories_set.add(row['Type'].strip())
    
    print(f"   Found locations: {locations_set}")
    print(f"   Found categories: {categories_set}")
    
    # Create locations if they don't exist
    for loc_name in locations_set:
        location, created = Location.objects.get_or_create(
            locationName=loc_name.upper()  # Store as uppercase (HCM, HANOI, etc.)
        )
        if created:
            print(f"   Created new location: {location.locationName}")
    
    # Step 3: Import destinations
    print("\n3. Importing destinations...")
    success_count = 0
    error_count = 0
    
    with open(csv_file_path, 'r', encoding=used_encoding) as file:
        csv_reader = csv.DictReader(file, delimiter=',')
        
        for idx, row in enumerate(csv_reader, start=1):
            try:
                # Get location
                location_name = row.get('Location', '').strip().upper()
                location = Location.objects.filter(locationName=location_name).first()
                
                if not location:
                    print(f"   Warning: Location '{location_name}' not found for destination '{row.get('Name')}'. Skipping...")
                    error_count += 1
                    continue
                
                # Parse rating
                rating = 0.0
                try:
                    rating = float(row.get('Ratings', 0))
                except:
                    rating = 0.0
                
                # Clean and prepare image URLs
                image_urls_raw = row.get('image_urls', '')
                # The CSV already has " ||| " as separator, so we keep it as is
                
                # Create destination with custom ID
                destination = Destinations.objects.create(
                    desName=row.get('Name', '').strip(),
                    destination_id=f"dest_{str(idx).zfill(3)}",
                    location=location,
                    description=row.get('Description', '').strip(),
                    category=row.get('Type', '').strip(),
                    rating=rating,
                    address=row.get('Address', '').strip(),
                    image_urls=image_urls_raw.strip(),
                    image_url=image_urls_raw.split('|||')[0].strip() if image_urls_raw else ''  # First image as main
                )
                
                success_count += 1
                if success_count % 10 == 0:
                    print(f"   Imported {success_count} destinations...")
                    
            except Exception as e:
                error_count += 1
                print(f"   Error importing row {idx}: {str(e)}")
                continue
    
    print(f"\n✅ Import completed!")
    print(f"   Successfully imported: {success_count} destinations")
    print(f"   Errors: {error_count}")
    print(f"   Total locations in database: {Location.objects.count()}")
    
    # Print sample destination to verify
    sample = Destinations.objects.first()
    if sample:
        print(f"\n📍 Sample destination:")
        print(f"   Name: {sample.desName}")
        print(f"   Category: {sample.category}")
        print(f"   Location: {sample.location.locationName if sample.location else 'N/A'}")
        print(f"   Rating: {sample.rating}")
        print(f"   Images: {len(sample.get_image_list())} URLs")

if __name__ == "__main__":
    csv_path = "data.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        print(f"   Current directory: {os.getcwd()}")
    else:
        import_destinations_from_csv(csv_path)
