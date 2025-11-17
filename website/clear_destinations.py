"""
Script xóa tất cả địa điểm trong database
CẢNH BÁO: Script này sẽ XÓA TẤT CẢ dữ liệu destinations!
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations, Region

print("\n" + "="*70)
print("⚠️  XÓA DỮ LIỆU DESTINATIONS".center(70))
print("="*70 + "\n")

# Đếm số lượng hiện tại
total_destinations = Destinations.objects.count()
total_regions = Region.objects.count()

print(f"📊 Hiện tại trong database:")
print(f"   - Destinations: {total_destinations}")
print(f"   - Regions: {total_regions}\n")

if total_destinations == 0:
    print("✅ Database đã trống rồi!")
else:
    print("⚠️  CẢNH BÁO: Bạn sắp xóa TẤT CẢ địa điểm!")
    confirm = input("👉 Gõ 'XOA' để xác nhận xóa: ").strip()
    
    if confirm == 'XOA':
        # Xóa tất cả destinations
        deleted_count = Destinations.objects.all().delete()[0]
        print(f"\n✅ Đã xóa {deleted_count} destinations")
        
        # Hỏi có muốn xóa regions không
        if total_regions > 0:
            confirm_regions = input("\n👉 Xóa luôn regions? (y/n): ").strip().lower()
            if confirm_regions == 'y':
                deleted_regions = Region.objects.all().delete()[0]
                print(f"✅ Đã xóa {deleted_regions} regions")
        
        print("\n" + "="*70)
        print("✅ XÓA DỮ LIỆU HOÀN TẤT!")
        print("="*70 + "\n")
    else:
        print("\n❌ Hủy bỏ. Không xóa gì cả.\n")
