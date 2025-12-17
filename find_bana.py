import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'website'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations

dests = Destinations.objects.filter(desName__icontains='Ba Na')
print('Found:', [d.desName for d in dests])
if dests:
    dest = dests[0]
    print('Images:', dest.get_image_list())
    print('Thumbnail:', dest.get_thumbnail_url())