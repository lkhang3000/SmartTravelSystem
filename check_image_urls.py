import os
import django
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations

def check_url(url):
    """Check if URL is accessible"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return url, response.status_code == 200
    except:
        return url, False

# Get all destinations with images
dests = Destinations.objects.exclude(image_urls__isnull=True).exclude(image_urls='')

print(f"Checking {len(dests)} destinations...")
broken_images = []
working_images = []

for dest in dests[:50]:  # Check first 50 destinations
    images = dest.get_image_list()
    if images:
        thumbnail = dest.get_thumbnail_url()
        print(f"\n{dest.desName}")
        print(f"  Thumbnail: {thumbnail}")
        
        # Check thumbnail URL
        if thumbnail:
            _, is_working = check_url(thumbnail)
            if is_working:
                print(f"  ✓ Thumbnail OK")
                working_images.append((dest.desName, thumbnail))
            else:
                print(f"  ✗ Thumbnail BROKEN")
                broken_images.append((dest.desName, thumbnail, images))

print(f"\n\n=== SUMMARY ===")
print(f"Working: {len(working_images)}")
print(f"Broken: {len(broken_images)}")

if broken_images:
    print(f"\n=== BROKEN IMAGES ===")
    for name, thumb, all_images in broken_images[:10]:
        print(f"\n{name}:")
        print(f"  Current thumbnail: {thumb}")
        print(f"  All images: {len(all_images)}")
        for i, img in enumerate(all_images[:3], 1):
            print(f"    {i}. {img}")
