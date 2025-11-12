"""
Management command để tự động gán region cho các destinations cũ
dựa trên thông tin location
"""
from django.core.management.base import BaseCommand
from sightseeing.models import Region, Destinations


class Command(BaseCommand):
    help = 'Tự động gán region cho các destinations chưa có region'

    def handle(self, *args, **kwargs):
        # Mapping location to region
        location_to_region = {
            'miền Bắc': ['Hà Nội', 'Hanoi', 'Hải Phòng', 'Quảng Ninh', 'Ninh Bình'],
            'Tây Bắc': ['Sa Pa', 'Sapa', 'Lào Cai'],
            'miền Trung': ['Đà Nẵng', 'Da Nang', 'Huế', 'Hội An', 'Quảng Nam'],
            'Tây Nguyên': ['Đà Lạt', 'Dalat', 'Lâm Đồng'],
            'miền Nam': ['Hồ Chí Minh', 'Sài Gòn', 'Saigon', 'Phú Quốc', 'Kiên Giang', 'Vũng Tàu']
        }
        
        # Tạo các regions nếu chưa có
        for region_name in location_to_region.keys():
            Region.objects.get_or_create(regionName=region_name)
        
        # Lấy destinations chưa có region
        destinations_without_region = Destinations.objects.filter(region__isnull=True)
        count = destinations_without_region.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ Tất cả destinations đã có region'))
            return
        
        self.stdout.write(f'Đang xử lý {count} destinations...')
        updated = 0
        
        for dest in destinations_without_region:
            location = dest.location or ''
            region_assigned = False
            
            # Tìm region phù hợp
            for region_name, cities in location_to_region.items():
                if any(city.lower() in location.lower() for city in cities):
                    region = Region.objects.get(regionName=region_name)
                    dest.region = region
                    dest.save()
                    self.stdout.write(f'✓ {dest.desName} → {region_name}')
                    updated += 1
                    region_assigned = True
                    break
            
            # Nếu không tìm thấy, gán mặc định là "miền Trung"
            if not region_assigned:
                default_region = Region.objects.get(regionName='miền Trung')
                dest.region = default_region
                dest.save()
                self.stdout.write(self.style.WARNING(f'⚠ {dest.desName} → miền Trung (mặc định)'))
                updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Đã cập nhật {updated} destinations'))
