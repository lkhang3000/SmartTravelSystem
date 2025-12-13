"""
Script to delete all Destinations and Hotels from database
Run: python delete_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations, Hotel

def delete_all_destinations_and_hotels():
    print("Deleting all destinations...")
    dest_count = Destinations.objects.count()
    Destinations.objects.all().delete()
    print(f"Deleted {dest_count} destinations")
    
    print("Deleting all hotels...")
    hotel_count = Hotel.objects.count()
    Hotel.objects.all().delete()
    print(f"Deleted {hotel_count} hotels")
    
    print("\nDone! All destinations and hotels have been deleted.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL destinations and hotels? (yes/no): ")
    if confirm.lower() == 'yes':
        delete_all_destinations_and_hotels()
    else:
        print("Operation cancelled.")
