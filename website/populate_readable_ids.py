import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations, Hotel, UsersProfile

def populate_readable_ids():
    # Clear existing IDs first
    Destinations.objects.update(destination_id=None)
    Hotel.objects.update(hotel_id=None)
    UsersProfile.objects.update(custom_user_id=None)

    # Populate destination_id for Destinations
    destinations = Destinations.objects.all().order_by('id')
    for i, dest in enumerate(destinations, 1):
        dest.destination_id = f"dest_{i:03d}"  # dest_001, dest_002, etc.
        dest.save()
    print(f"Populated destination_id for {destinations.count()} Destinations")

    # Populate hotel_id for Hotel
    hotels = Hotel.objects.all().order_by('id')
    for i, hotel in enumerate(hotels, 1):
        hotel.hotel_id = f"hotel_{i:03d}"  # hotel_001, hotel_002, etc.
        hotel.save()
    print(f"Populated hotel_id for {hotels.count()} Hotels")

    # Populate custom_user_id for UsersProfile
    users = UsersProfile.objects.all().order_by('id')
    for i, user in enumerate(users, 1):
        user.custom_user_id = f"user_{i:03d}"  # user_001, user_002, etc.
        user.save()
    print(f"Populated custom_user_id for {users.count()} UsersProfiles")

if __name__ == '__main__':
    populate_readable_ids()