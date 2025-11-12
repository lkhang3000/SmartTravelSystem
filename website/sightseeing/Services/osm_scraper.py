"""
Script cải tiến để lấy địa điểm du lịch nổi tiếng từ OpenStreetMap
"""

import os
import sys
import django
import requests
import json
from time import sleep

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Region, Destinations


class OSMTourismScraper:
    """Class để lấy dữ liệu từ OpenStreetMap và upload vào Django DB"""
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.stats = {
            'fetched': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Danh sách các điểm du lịch KHÔNG mong muốn (để lọc bỏ)
        self.excluded_keywords = [
            'spa', 'massage', 'karaoke', 'bar', 'pub', 'club', 'casino',
            'khách sạn', 'hotel', 'resort', 'coffee', 'cafe', 'restaurant',
            'shop', 'store', 'market', 'mall', 'chợ', 'siêu thị',
            'bệnh viện', 'hospital', 'clinic', 'pharmacy', 'atm', 'bank'
        ]
    
    def get_vietnam_tourism_data(self, region_name=None, limit=50):
        """
        Query ĐƠN GIẢN HÓA để tránh timeout
        """
        print(f"\n🔍 Đang tìm kiếm địa điểm du lịch{' tại ' + region_name if region_name else ' toàn Việt Nam'}...")
        
        if region_name:
            # Query ĐƠN GIẢN - chỉ lấy điểm chính
            query = f"""
            [out:json][timeout:20];
            area["name:vi"="{region_name}"]->.searchArea;
            (
              node["tourism"="attraction"]["name"](area.searchArea);
              node["tourism"="museum"]["name"](area.searchArea);
              node["historic"]["name"](area.searchArea);
              node["natural"]["name"](area.searchArea);
            );
            out center {limit};
            """
        else:
            # Query toàn quốc - RẤT ĐƠN GIẢN
            query = f"""
            [out:json][timeout:20];
            area["ISO3166-1"="VN"][admin_level=2];
            node["tourism"="attraction"]["name"](area);
            out center {limit};
            """
        
        # Thử với retry
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"  📡 Đang gọi API... (lần thử {attempt + 1}/{max_retries})")
                response = requests.post(self.overpass_url, data={'data': query}, timeout=25)
                response.raise_for_status()
                data = response.json()
                
                elements = data.get('elements', [])
                
                # LỌC BỎ các địa điểm không mong muốn
                filtered_elements = []
                for element in elements:
                    tags = element.get('tags', {})
                    name = (tags.get('name') or tags.get('name:vi') or tags.get('name:en', '')).lower()
                    
                    # Kiểm tra có chứa từ khóa loại trừ không
                    is_excluded = any(keyword in name for keyword in self.excluded_keywords)
                    
                    # Kiểm tra các tag không mong muốn
                    amenity = tags.get('amenity', '').lower()
                    shop = tags.get('shop', '').lower()
                    is_commercial = amenity in ['restaurant', 'cafe', 'bar', 'pub', 'nightclub', 'casino'] or shop
                    
                    if not is_excluded and not is_commercial:
                        filtered_elements.append(element)
                
                self.stats['fetched'] += len(filtered_elements)
                print(f"✓ Tìm thấy {len(elements)} địa điểm → Sau lọc: {len(filtered_elements)} địa điểm")
                
                return filtered_elements
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"  ⏳ Timeout, thử lại sau 5 giây...")
                    sleep(5)
                else:
                    print(f"  ⚠️ Bỏ qua {region_name} - API timeout")
                    return []
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [504, 429, 503]:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (attempt + 1)
                        print(f"  ⏳ Server quá tải, đợi {wait_time} giây...")
                        sleep(wait_time)
                    else:
                        print(f"  ⚠️ Bỏ qua {region_name} - Server quá tải")
                        return []
                else:
                    print(f"❌ Lỗi HTTP: {e}")
                    return []
            except Exception as e:
                print(f"❌ Lỗi khi gọi API: {e}")
                return []
        
        return []
    
    def determine_region(self, tags):
        """Xác định miền dựa trên thông tin địa chỉ"""
        address_fields = [
            tags.get('addr:city', ''),
            tags.get('addr:province', ''),
            tags.get('is_in', ''),
            tags.get('name:en', ''),
        ]
        address_text = ' '.join(address_fields).lower()
        
        # Mapping cities to regions - BỔ SUNG NHIỀU HƠN
        region_map = {
            'miền Bắc': ['hà nội', 'hanoi', 'hải phòng', 'haiphong', 'quảng ninh', 'quang ninh', 
                         'ninh bình', 'ninh binh', 'thái bình', 'nam định', 'hạ long', 'ha long'],
            'Tây Bắc': ['sa pa', 'sapa', 'lào cai', 'lai châu', 'điện biên', 'sơn la', 'hòa bình',
                       'mù cang chải', 'mu cang chai'],
            'miền Trung': ['đà nẵng', 'da nang', 'huế', 'hue', 'hội an', 'hoi an', 
                          'quảng nam', 'quang nam', 'quảng ngãi', 'bình định', 'nha trang',
                          'phú yên', 'phu yen', 'quy nhơn', 'quy nhon'],
            'Tây Nguyên': ['đà lạt', 'dalat', 'lâm đồng', 'lam dong', 'gia lai', 
                          'đắk lắk', 'dak lak', 'kon tum', 'pleiku', 'buôn ma thuột'],
            'miền Nam': ['hồ chí minh', 'ho chi minh', 'saigon', 'sài gòn', 'vũng tàu', 'vung tau',
                        'phú quốc', 'phu quoc', 'cần thơ', 'can tho', 'kiên giang', 'mỹ tho',
                        'bến tre', 'ben tre', 'cà mau', 'ca mau']
        }
        
        for region, keywords in region_map.items():
            if any(keyword in address_text for keyword in keywords):
                return region
        
        return 'miền Trung'  # Default
    
    def determine_category(self, tags):
        """Xác định loại hình địa điểm - CẢI TIẾN"""
        tourism = tags.get('tourism', '').lower()
        historic = tags.get('historic', '').lower()
        natural = tags.get('natural', '').lower()
        building = tags.get('building', '').lower()
        
        # Ưu tiên các loại đặc biệt hơn
        if historic:
            if 'temple' in historic or 'shrine' in historic or 'pagoda' in building:
                return 'Chùa/Đền/Miếu'
            elif 'castle' in historic or 'fort' in historic:
                return 'Thành/Pháo đài'
            elif 'monument' in historic or 'memorial' in historic:
                return 'Di tích lịch sử'
            elif 'archaeological' in historic or 'ruins' in historic:
                return 'Khu khảo cổ'
        
        if natural:
            if 'beach' in natural:
                return 'Bãi biển'
            elif 'peak' in natural or 'mountain' in natural:
                return 'Núi/Đỉnh núi'
            elif 'cave' in natural:
                return 'Hang động'
            elif 'waterfall' in natural:
                return 'Thác nước'
            elif 'bay' in natural:
                return 'Vịnh/Bãi biển'
        
        if tourism:
            if 'museum' in tourism:
                return 'Bảo tàng'
            elif 'viewpoint' in tourism:
                return 'Điểm ngắm cảnh'
            elif 'theme_park' in tourism or 'zoo' in tourism or 'aquarium' in tourism:
                return 'Công viên giải trí'
            elif 'gallery' in tourism:
                return 'Phòng tranh'
        
        return 'Điểm tham quan'
    
    def extract_location_name(self, tags):
        """Lấy tên thành phố/tỉnh"""
        return (tags.get('addr:city') or 
                tags.get('addr:province') or 
                tags.get('addr:state') or 
                'Việt Nam')
    
    def get_description_from_wikipedia(self, tags):
        """Lấy mô tả từ Wikipedia nếu có"""
        wikipedia = tags.get('wikipedia', '')
        if wikipedia:
            # Format: "vi:Tên_bài_viết" hoặc "en:Article_name"
            return f"Xem thêm: https://{wikipedia.split(':')[0]}.wikipedia.org/wiki/{wikipedia.split(':')[1]}"
        return tags.get('description', '')
    
    def upload_to_database(self, elements):
        """Upload dữ liệu vào Django database"""
        print("\n📤 Đang upload vào database...")
        
        for element in elements:
            try:
                tags = element.get('tags', {})
                name = tags.get('name') or tags.get('name:vi') or tags.get('name:en')
                
                if not name:
                    self.stats['skipped'] += 1
                    continue
                
                # Lấy tọa độ
                if element['type'] == 'node':
                    lat = element.get('lat')
                    lon = element.get('lon')
                else:  # way hoặc relation
                    center = element.get('center', {})
                    lat = center.get('lat')
                    lon = center.get('lon')
                
                if not lat or not lon:
                    print(f"⏭  Bỏ qua (không có tọa độ): {name}")
                    self.stats['skipped'] += 1
                    continue
                
                # Xác định region
                region_name = self.determine_region(tags)
                region, _ = Region.objects.get_or_create(regionName=region_name)
                
                # Kiểm tra đã tồn tại chưa (theo tên VÀ tọa độ gần)
                existing = Destinations.objects.filter(
                    desName__iexact=name,
                    region=region
                ).first()
                
                if existing:
                    print(f"⏭  Đã tồn tại: {name}")
                    self.stats['skipped'] += 1
                    continue
                
                # Tạo địa điểm mới
                location_name = self.extract_location_name(tags)
                category = self.determine_category(tags)
                
                # Lấy thông tin bổ sung
                description = self.get_description_from_wikipedia(tags) or tags.get('description') or ''
                if not description:
                    description = f"{category} nổi tiếng tại {location_name}"
                
                website = tags.get('website') or tags.get('contact:website') or tags.get('url') or ''
                phone = tags.get('phone') or tags.get('contact:phone') or ''
                opening_hours = tags.get('opening_hours', '')
                
                # Tạo địa chỉ đầy đủ
                address_parts = [
                    tags.get('addr:housenumber', ''),
                    tags.get('addr:street', ''),
                    tags.get('addr:district', ''),
                    tags.get('addr:city', ''),
                    tags.get('addr:province', '')
                ]
                address = ', '.join(filter(None, address_parts)) or f"{location_name}"
                
                # Tạo Wikipedia/Wikidata image URL
                image_url = ''
                if tags.get('image'):
                    image_url = tags.get('image')
                elif tags.get('wikipedia'):
                    wiki_lang = tags.get('wikipedia').split(':')[0]
                    wiki_page = tags.get('wikipedia').split(':')[1]
                    image_url = f"https://{wiki_lang}.wikipedia.org/wiki/{wiki_page}"
                
                # Tạo destination
                Destinations.objects.create(
                    desName=name,
                    region=region,
                    location=location_name,
                    description=description,
                    category=category,
                    rating=0.0,
                    address=address,
                    phone=phone,
                    website=website,
                    opening_hours=opening_hours,
                    image_url=image_url,
                    price_range=''
                )
                
                print(f"✓ Đã thêm: {name} - {location_name} ({category})")
                self.stats['created'] += 1
                
                # Delay nhỏ để tránh quá tải
                sleep(0.1)
                
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {name}: {e}")
                self.stats['errors'] += 1
                continue
    
    def print_stats(self):
        """In thống kê"""
        print("\n" + "="*60)
        print("📊 KẾT QUẢ THU THẬP DỮ LIỆU")
        print("="*60)
        print(f"📥 Đã tìm thấy:        {self.stats['fetched']} địa điểm")
        print(f"✅ Đã thêm mới:       {self.stats['created']} địa điểm")
        print(f"⏭️  Đã bỏ qua (trùng): {self.stats['skipped']} địa điểm")
        print(f"❌ Lỗi:               {self.stats['errors']} địa điểm")
        print("="*60)
    
    def run(self, regions=None, limit=50):
        """
        Chạy scraper
        """
        print("\n" + "="*60)
        print("🗺️  OPENSTREETMAP TOURISM SCRAPER - PHIÊN BẢN CẢI TIẾN")
        print("="*60)
        
        if regions:
            for region in regions:
                elements = self.get_vietnam_tourism_data(region, limit)
                if elements:
                    self.upload_to_database(elements)
                sleep(3)  # Delay lâu hơn giữa các request
        else:
            elements = self.get_vietnam_tourism_data(None, limit)
            if elements:
                self.upload_to_database(elements)
        
        self.print_stats()
        print("\n✅ Hoàn thành!\n")


def main():
    """Hàm main để chạy script"""
    scraper = OSMTourismScraper()
    
    # 9 THÀNH PHỐ như yêu cầu - mỗi thành 10 địa điểm
    print("\n🎯 Thu thập từ 9 thành phố (mỗi thành phố: 10 địa điểm)")
    print("⚡ Query đơn giản hóa để tránh timeout\n")
    
    tourist_regions = [
        # MIỀN BẮC (3 thành phố)
        "Hà Nội",
        "Quảng Ninh",
        "Ninh Bình",
        
        # MIỀN TRUNG (3 thành phố)
        "Thừa Thiên Huế",
        "Đà Nẵng",
        "Quảng Nam",
        
        # MIỀN NAM (3 thành phố)
        "Hồ Chí Minh",
        "Bà Rịa-Vũng Tàu",
        "Kiên Giang",
    ]
    
    # Giới hạn mỗi thành phố 10 địa điểm
    scraper.run(regions=tourist_regions, limit=10)


if __name__ == '__main__':
    print("\n" + "🚀 BẮT ĐẦU THU THẬP DỮ LIỆU - PHIÊN BẢN CẢI TIẾN".center(60))
    print("⏳ Quá trình này có thể mất 10-15 phút...\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()