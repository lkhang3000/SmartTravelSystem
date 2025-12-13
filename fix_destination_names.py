import os
import django
import sys

# Add website folder to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'website'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations

def replace_parentheses_with_dash():
    print("Replacing parentheses with dashes in destination names...")
    
    # Get all destinations with parentheses in name
    destinations = Destinations.objects.all()
    updated_count = 0
    
    for dest in destinations:
        if '(' in dest.desName and ')' in dest.desName:
            old_name = dest.desName
            # Replace (text) with - text
            new_name = dest.desName.replace('(', '- ').replace(')', '')
            # Clean up extra spaces
            new_name = ' '.join(new_name.split())
            
            dest.desName = new_name
            dest.save()
            
            updated_count += 1
            print(f"✅ {old_name} → {new_name}")
    
    print(f"\n✅ Updated {updated_count} destinations")

if __name__ == "__main__":
    replace_parentheses_with_dash()
