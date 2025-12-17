import os
import sys
import django

# Add the website directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'website'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations

dests = Destinations.objects.all()
print(f'Total destinations: {dests.count()}')

missing_images = []
for d in dests:
    if not d.image_urls and not d.image_url:
        missing_images.append(d.desName)
    else:
        print(f'{d.desName}: image_urls={d.image_urls}, image_url={d.image_url}')

print(f'\nDestinations without images: {len(missing_images)}')
for name in missing_images[:10]:  # Show first 10
    print(f'- {name}')