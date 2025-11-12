"""
SCRIPT ĐƠN GIẢN - Thu thập dữ liệu địa điểm du lịch Việt Nam
Nguồn: OpenStreetMap (miễn phí, không cần API key)
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.Services.osm_scraper import OSMTourismScraper

print("\n" + "="*70)
print("🗺️  THU THẬP DỮ LIỆU TỪ OPENSTREETMAP".center(70))
print("="*70 + "\n")

# Chạy scraper
scraper = OSMTourismScraper()

# Lấy dữ liệu từ các thành phố du lịch
cities = ["Hà Nội", "Đà Nẵng", "Hồ Chí Minh", "Quảng Ninh", "Lâm Đồng", "Sa Pa"]

print(f"� Đang thu thập từ: {', '.join(cities)}")
print("⏳ Quá trình có thể mất 3-5 phút...\n")

scraper.run(regions=cities, limit=20)

print("\n✅ HOÀN THÀNH! Dữ liệu đã được upload vào database.")
print("💡 Xem kết quả: python manage.py shell")
print("   >>> from sightseeing.models import Destinations")
print("   >>> print(f'Tổng: {Destinations.objects.count()} địa điểm')\n")
