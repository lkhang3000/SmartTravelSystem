import os
import sys
sys.path.append('D:\\SmartTravel\\website')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
import django
django.setup()
from sightseeing.models import TripItem
print('Total TripItem:', TripItem.objects.count())
print('Saved (trip__isnull=True):', TripItem.objects.filter(trip__isnull=True).count())
print('In trips:', TripItem.objects.filter(trip__isnull=False).count())