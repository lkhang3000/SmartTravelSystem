from sightseeing.models import Destinations, Location
from django.db.models import Count

# Kiểm tra tổng số destinations
total = Destinations.objects.count()
print(f'Total destinations: {total}')

# Tìm trùng lặp theo desName
duplicates_by_name = Destinations.objects.values('desName').annotate(count=Count('id')).filter(count__gt=1, desName__isnull=False)
print(f'\nDuplicate destinations by name ({duplicates_by_name.count()} groups):')
for dup in duplicates_by_name[:10]:  # Hiển thị 10 đầu tiên
    print(f'{dup["desName"]}: {dup["count"]} times')

# Tìm trùng lặp theo location
duplicates_by_location = Destinations.objects.values('location__locationName').annotate(count=Count('id')).filter(count__gt=1, location__isnull=False)
print(f'\nDuplicate destinations by location ({duplicates_by_location.count()} groups):')
for dup in duplicates_by_location[:10]:
    print(f'{dup["location__locationName"]}: {dup["count"]} destinations')

# Kiểm tra Location trùng lặp
location_duplicates = Location.objects.values('locationName').annotate(count=Count('id')).filter(count__gt=1, locationName__isnull=False)
print(f'\nDuplicate locations ({location_duplicates.count()} groups):')
for dup in location_duplicates[:10]:
    print(f'{dup["locationName"]}: {dup["count"]} times')