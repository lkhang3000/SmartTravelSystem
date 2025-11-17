"""
Script to update images for all destinations
Provides multiple options for image URLs
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations

def option_1_unsplash():
    """Option 1: Use Unsplash API (requires API key)"""
    print("\n" + "="*70)
    print("OPTION 1: UNSPLASH API")
    print("="*70)
    print("Requires Unsplash API key")
    print("Sign up at: https://unsplash.com/developers")
    print("\nExample URL: https://source.unsplash.com/800x600/?{keyword}")
    
    api_key = input("\nEnter your Unsplash API key (or press Enter to skip): ")
    if not api_key:
        print("Skipped.")
        return
    
    count = 0
    for dest in Destinations.objects.all():
        keyword = dest.category or dest.desName
        dest.image_url = f"https://source.unsplash.com/800x600/?{keyword.replace(' ', '+')}"
        dest.save()
        count += 1
        print(f"✅ Updated: {dest.desName}")
    
    print(f"\n✅ Updated {count} destinations with Unsplash images")

def option_2_picsum():
    """Option 2: Use Picsum Photos (stable URLs based on destination name)"""
    print("\n" + "="*70)
    print("OPTION 2: PICSUM PHOTOS (RECOMMENDED)")
    print("="*70)
    print("Free placeholder images with stable URLs")
    print("Each destination gets a unique consistent image")
    
    response = input("\nUpdate all destinations with Picsum? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipped.")
        return
    
    count = 0
    for dest in Destinations.objects.all():
        # Create stable seed based on destination name
        seed = abs(hash(dest.desName)) % 10000
        dest.image_url = f"https://picsum.photos/seed/{seed}/800/600"
        dest.save()
        count += 1
        print(f"✅ Updated: {dest.desName} -> seed {seed}")
    
    print(f"\n✅ Updated {count} destinations with Picsum images")

def option_3_upload_local():
    """Option 3: Prepare for local image upload"""
    print("\n" + "="*70)
    print("OPTION 3: LOCAL IMAGES")
    print("="*70)
    print("Upload images to: website/sightseeing/Static/images/destinations/")
    print("\nFile naming convention:")
    print("  - Use location-name.jpg format")
    print("  - Example: ha-noi-old-quarter.jpg")
    print("  - Or: hanoi-{id}.jpg")
    
    print("\nGenerating image mapping file...")
    
    with open('image_mapping.txt', 'w', encoding='utf-8') as f:
        f.write("DESTINATION ID MAPPING FOR IMAGE UPLOAD\n")
        f.write("="*70 + "\n\n")
        
        for dest in Destinations.objects.all():
            location_name = dest.location.locationName if dest.location else "Unknown"
            suggested_filename = f"{dest.id}.jpg"
            f.write(f"ID: {dest.id}\n")
            f.write(f"Name: {dest.desName}\n")
            f.write(f"Location: {location_name}\n")
            f.write(f"Suggested filename: {suggested_filename}\n")
            f.write(f"URL will be: /static/images/destinations/{suggested_filename}\n")
            f.write("-"*70 + "\n\n")
    
    print("✅ Created image_mapping.txt")
    print("\nNext steps:")
    print("1. Create folder: website/sightseeing/Static/images/destinations/")
    print("2. Upload images with names from image_mapping.txt")
    print("3. Run: python update_images.py --apply-local")

def option_4_apply_local():
    """Option 4: Apply local image URLs"""
    print("\n" + "="*70)
    print("OPTION 4: APPLY LOCAL IMAGE URLS")
    print("="*70)
    
    img_folder = os.path.join('sightseeing', 'Static', 'images', 'destinations')
    if not os.path.exists(img_folder):
        print(f"❌ Folder not found: {img_folder}")
        print("Create it first and add images!")
        return
    
    count = 0
    for dest in Destinations.objects.all():
        # Try multiple filename patterns
        patterns = [
            f"{dest.id}.jpg",
            f"{dest.id}.png",
            f"{dest.desName.lower().replace(' ', '-')}.jpg",
            f"{dest.desName.lower().replace(' ', '-')}.png",
        ]
        
        for pattern in patterns:
            filepath = os.path.join(img_folder, pattern)
            if os.path.exists(filepath):
                dest.image_url = f"/static/images/destinations/{pattern}"
                dest.save()
                count += 1
                print(f"✅ Updated: {dest.desName} -> {pattern}")
                break
    
    print(f"\n✅ Updated {count} destinations with local images")

def option_5_custom_url():
    """Option 5: Use custom URL pattern"""
    print("\n" + "="*70)
    print("OPTION 5: CUSTOM URL PATTERN")
    print("="*70)
    print("Use your own CDN or image server")
    print("\nAvailable variables:")
    print("  {id} - Destination ID")
    print("  {name} - Destination name")
    print("  {location} - Location name")
    
    pattern = input("\nEnter URL pattern (e.g., https://mycdn.com/images/{id}.jpg): ")
    if not pattern:
        print("Skipped.")
        return
    
    count = 0
    for dest in Destinations.objects.all():
        location_name = dest.location.locationName if dest.location else "unknown"
        url = pattern.format(
            id=dest.id,
            name=dest.desName.lower().replace(' ', '-'),
            location=location_name.lower().replace(' ', '-')
        )
        dest.image_url = url
        dest.save()
        count += 1
        print(f"✅ Updated: {dest.desName}")
    
    print(f"\n✅ Updated {count} destinations")

def show_stats():
    """Show current image statistics"""
    total = Destinations.objects.count()
    with_images = Destinations.objects.exclude(image_url__isnull=True).exclude(image_url='').count()
    without_images = total - with_images
    
    print("\n" + "="*70)
    print("CURRENT IMAGE STATISTICS")
    print("="*70)
    print(f"Total destinations: {total}")
    print(f"With images: {with_images}")
    print(f"Without images: {without_images}")
    
    if with_images > 0:
        print("\nSample image URLs:")
        for dest in Destinations.objects.exclude(image_url__isnull=True).exclude(image_url='')[:5]:
            print(f"  {dest.desName}: {dest.image_url}")

def main():
    print("\n" + "="*70)
    print("UPDATE DESTINATION IMAGES")
    print("="*70)
    
    # Check if --apply-local flag
    if '--apply-local' in sys.argv:
        option_4_apply_local()
        return
    
    show_stats()
    
    print("\nChoose an option:")
    print("1. Unsplash API (requires API key)")
    print("2. Picsum Photos (RECOMMENDED - stable free images)")
    print("3. Prepare for local image upload")
    print("4. Apply local images (if already uploaded)")
    print("5. Custom URL pattern")
    print("0. Show statistics only")
    
    choice = input("\nEnter your choice (0-5): ")
    
    if choice == '1':
        option_1_unsplash()
    elif choice == '2':
        option_2_picsum()
    elif choice == '3':
        option_3_upload_local()
    elif choice == '4':
        option_4_apply_local()
    elif choice == '5':
        option_5_custom_url()
    elif choice == '0':
        pass
    else:
        print("Invalid choice!")
        return
    
    # Show stats after update
    show_stats()

if __name__ == '__main__':
    main()
