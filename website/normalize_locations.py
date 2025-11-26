from django.db import transaction
from sightseeing.models import Location, Destinations, Hotel

# Script chuẩn hóa Location: gộp các location trùng tên, cập nhật liên kết cho Hotel/Destinations
with transaction.atomic():
    name_map = {}
    deleted = 0
    updated_dest = 0
    updated_hotel = 0
    for loc in Location.objects.all():
        norm_name = loc.locationName.strip().title()
        if norm_name in name_map:
            main_loc = name_map[norm_name]
            # Cập nhật Destinations
            for dest in Destinations.objects.filter(location=loc):
                dest.location = main_loc
                dest.save()
                updated_dest += 1
            # Cập nhật Hotel
            for hotel in Hotel.objects.filter(location=loc):
                hotel.location = main_loc
                hotel.save()
                updated_hotel += 1
            loc.delete()
            deleted += 1
        else:
            loc.locationName = norm_name
            loc.save()
            name_map[norm_name] = loc
    print(f"Đã xóa {deleted} location trùng lặp. Đã cập nhật {updated_dest} destinations, {updated_hotel} hotels.")
