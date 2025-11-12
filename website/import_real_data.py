"""
Script thêm dữ liệu địa điểm du lịch thực từ dữ liệu có sẵn
Không cần API - dữ liệu từ nguồn chính thức
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Region, Destinations


# Dữ liệu thực từ các nguồn du lịch Việt Nam
VIETNAM_DESTINATIONS = [
    # MIỀN BẮC
    {
        "name": "Vịnh Hạ Long",
        "location": "Quảng Ninh",
        "region": "miền Bắc",
        "category": "Di sản thiên nhiên thế giới",
        "rating": 4.9,
        "description": "Di sản thiên nhiên thế giới với hàng nghìn hòn đảo đá vôi kỳ vĩ, nổi tiếng với cảnh quan tuyệt đẹp và hang động kỳ thú",
        "address": "Vịnh Hạ Long, Thành phố Hạ Long, Quảng Ninh",
        "price_range": "200,000 - 5,000,000 VNĐ (tùy tour)",
        "opening_hours": "24/7 (tour thường 7:00 - 18:00)"
    },
    {
        "name": "Hoàng Thành Thăng Long",
        "location": "Hà Nội",
        "region": "miền Bắc",
        "category": "Di sản văn hóa thế giới",
        "rating": 4.5,
        "description": "Di tích lịch sử quốc gia đặc biệt, trung tâm quyền lực của nhiều triều đại phong kiến Việt Nam",
        "address": "19C Hoàng Diệu, Điện Biên, Ba Đình, Hà Nội",
        "phone": "024 3734 5427",
        "price_range": "30,000 VNĐ",
        "opening_hours": "8:00 - 17:00 (Đóng cửa thứ 2)"
    },
    {
        "name": "Chùa Một Cột",
        "location": "Hà Nội",
        "region": "miền Bắc",
        "category": "Di tích lịch sử",
        "rating": 4.3,
        "description": "Ngôi chùa cổ nổi tiếng với kiến trúc độc đáo, biểu tượng của Hà Nội ngàn năm văn hiến",
        "address": "Chùa Một Cột, Đội Cấn, Ba Đình, Hà Nội",
        "price_range": "Miễn phí",
        "opening_hours": "7:00 - 18:00"
    },
    {
        "name": "Hồ Hoàn Kiếm",
        "location": "Hà Nội",
        "region": "miền Bắc",
        "category": "Điểm tham quan",
        "rating": 4.6,
        "description": "Trung tâm lịch sử và văn hóa của Hà Nội, nơi có Tháp Rùa và đền Ngọc Sơn",
        "address": "Hoàn Kiếm, Hà Nội",
        "price_range": "Miễn phí (vào đền: 30,000 VNĐ)",
        "opening_hours": "24/7"
    },
    {
        "name": "Tràng An",
        "location": "Ninh Bình",
        "region": "miền Bắc",
        "category": "Di sản thiên nhiên và văn hóa",
        "rating": 4.8,
        "description": "Quần thể danh thắng Tràng An - Di sản văn hóa và thiên nhiên thế giới, nổi tiếng với phong cảnh sông nước hữu tình",
        "address": "Tràng An, Ninh Bình",
        "phone": "0229 3618 010",
        "price_range": "250,000 VNĐ",
        "opening_hours": "7:00 - 17:00"
    },
    
    # TÂY BẮC
    {
        "name": "Fansipan",
        "location": "Sa Pa",
        "region": "Tây Bắc",
        "category": "Đỉnh núi",
        "rating": 4.9,
        "description": "Nóc nhà Đông Dương - đỉnh núi cao nhất Việt Nam và Đông Dương (3,143m), có cáp treo hiện đại",
        "address": "Sa Pa, Lào Cai",
        "price_range": "700,000 - 850,000 VNĐ (cáp treo)",
        "opening_hours": "7:30 - 17:30"
    },
    {
        "name": "Bản Cát Cát",
        "location": "Sa Pa",
        "region": "Tây Bắc",
        "category": "Làng văn hóa",
        "rating": 4.5,
        "description": "Làng văn hóa người H'Mông đen, nơi lưu giữ nét văn hóa truyền thống với nghề dệt lanh nhuộm chàm",
        "address": "Sa Pa, Lào Cai",
        "price_range": "70,000 VNĐ",
        "opening_hours": "6:00 - 18:00"
    },
    
    # MIỀN TRUNG
    {
        "name": "Phố Cổ Hội An",
        "location": "Quảng Nam",
        "region": "miền Trung",
        "category": "Di sản văn hóa thế giới",
        "rating": 4.8,
        "description": "Thành phố cổ được UNESCO công nhận, nổi tiếng với kiến trúc cổ kính và đèn lồng rực rỡ",
        "address": "Phố cổ Hội An, Quảng Nam",
        "price_range": "120,000 VNĐ (vé tham quan 5 điểm)",
        "opening_hours": "24/7"
    },
    {
        "name": "Bà Nà Hills",
        "location": "Đà Nẵng",
        "region": "miền Trung",
        "category": "Khu du lịch",
        "rating": 4.7,
        "description": "Khu du lịch nổi tiếng với Cầu Vàng được nâng đỡ bởi đôi bàn tay khổng lồ, cáp treo dài nhất thế giới",
        "address": "Hòa Vang, Đà Nẵng",
        "phone": "0236 3791 999",
        "website": "https://banahills.sunworld.vn",
        "price_range": "700,000 - 850,000 VNĐ",
        "opening_hours": "7:00 - 22:00"
    },
    {
        "name": "Bãi Biển Mỹ Khê",
        "location": "Đà Nẵng",
        "region": "miền Trung",
        "category": "Bãi biển",
        "rating": 4.8,
        "description": "Một trong những bãi biển đẹp nhất hành tinh theo Forbes, nước trong xanh, cát trắng mịn",
        "address": "Phường Phước Mỹ, Sơn Trà, Đà Nẵng",
        "price_range": "Miễn phí",
        "opening_hours": "24/7"
    },
    {
        "name": "Cố đô Huế",
        "location": "Huế",
        "region": "miền Trung",
        "category": "Di sản văn hóa thế giới",
        "rating": 4.7,
        "description": "Quần thể di tích cố đô Huế - kinh đô của triều Nguyễn, di sản văn hóa thế giới",
        "address": "Thành phố Huế, Thừa Thiên Huế",
        "phone": "0234 3523 237",
        "price_range": "200,000 VNĐ",
        "opening_hours": "7:00 - 17:30"
    },
    {
        "name": "Động Phong Nha",
        "location": "Quảng Bình",
        "region": "miền Trung",
        "category": "Di sản thiên nhiên thế giới",
        "rating": 4.9,
        "description": "Hang động thuộc Vườn quốc gia Phong Nha - Kẻ Bàng, Di sản thiên nhiên thế giới, nổi tiếng với nhũ đá kỳ vĩ",
        "address": "Bố Trạch, Quảng Bình",
        "phone": "0232 3677 021",
        "price_range": "150,000 - 300,000 VNĐ",
        "opening_hours": "7:00 - 16:00"
    },
    
    # TÂY NGUYÊN
    {
        "name": "Hồ Xuân Hương",
        "location": "Đà Lạt",
        "region": "Tây Nguyên",
        "category": "Hồ nước",
        "rating": 4.6,
        "description": "Hồ nước ngọt đẹp như tranh giữa lòng Đà Lạt, nơi lý tưởng để dạo chơi và chụp ảnh",
        "address": "Trung tâm thành phố Đà Lạt, Lâm Đồng",
        "price_range": "Miễn phí",
        "opening_hours": "24/7"
    },
    {
        "name": "Thác Datanla",
        "location": "Đà Lạt",
        "region": "Tây Nguyên",
        "category": "Thác nước",
        "rating": 4.5,
        "description": "Thác nước đẹp với hệ thống trò chơi cảm giác mạnh như xe lượn ống trượt Alpine Coaster",
        "address": "Đèo Prenn, Đà Lạt, Lâm Đồng",
        "phone": "0263 3831 804",
        "price_range": "50,000 - 200,000 VNĐ",
        "opening_hours": "7:00 - 17:00"
    },
    
    # MIỀN NAM
    {
        "name": "Dinh Độc Lập",
        "location": "Hồ Chí Minh",
        "region": "miền Nam",
        "category": "Di tích lịch sử",
        "rating": 4.6,
        "description": "Di tích lịch sử quan trọng đánh dấu mốc thống nhất đất nước, kiến trúc độc đáo thời hiện đại",
        "address": "135 Nam Kỳ Khởi Nghĩa, Quận 1, TP. Hồ Chí Minh",
        "phone": "028 3822 3652",
        "price_range": "65,000 VNĐ",
        "opening_hours": "7:30 - 11:00, 13:00 - 16:00"
    },
    {
        "name": "Nhà thờ Đức Bà",
        "location": "Hồ Chí Minh",
        "region": "miền Nam",
        "category": "Kiến trúc tôn giáo",
        "rating": 4.5,
        "description": "Nhà thờ Công giáo cổ nhất Sài Gòn, kiến trúc Gothic Romano đẹp mắt, biểu tượng của thành phố",
        "address": "01 Công xã Paris, Quận 1, TP. Hồ Chí Minh",
        "price_range": "Miễn phí",
        "opening_hours": "8:00 - 11:00, 15:00 - 16:00"
    },
    {
        "name": "Bãi Sao",
        "location": "Phú Quốc",
        "region": "miền Nam",
        "category": "Bãi biển",
        "rating": 4.9,
        "description": "Bãi biển đẹp nhất Phú Quốc với cát trắng mịn như bột, nước biển trong xanh ngọc bích",
        "address": "An Thới, Phú Quốc, Kiên Giang",
        "price_range": "Miễn phí",
        "opening_hours": "24/7"
    },
    {
        "name": "Chợ Nổi Cái Răng",
        "location": "Cần Thơ",
        "region": "miền Nam",
        "category": "Chợ nổi",
        "rating": 4.7,
        "description": "Chợ nổi lớn nhất miền Tây, nơi giao thương sầm uất trên sông nước, văn hóa đặc trưng của đồng bằng sông Cửu Long",
        "address": "Sông Cần Thơ, Cái Răng, Cần Thơ",
        "price_range": "200,000 - 500,000 VNĐ (tour thuyền)",
        "opening_hours": "5:00 - 9:00 (sáng sớm nhộn nhịp nhất)"
    },
    {
        "name": "Bãi Dài",
        "location": "Nha Trang",
        "region": "miền Trung",
        "category": "Bãi biển",
        "rating": 4.7,
        "description": "Bãi biển dài và đẹp, nước trong xanh, cát trắng mịn, lý tưởng cho nghỉ dưỡng",
        "address": "Cam Lâm, Khánh Hòa",
        "price_range": "Miễn phí",
        "opening_hours": "24/7"
    },
]


def import_destinations():
    """Import dữ liệu vào database"""
    print("\n" + "="*70)
    print("📥 IMPORT DỮ LIỆU ĐỊA ĐIỂM DU LỊCH VIỆT NAM".center(70))
    print("="*70 + "\n")
    
    created = 0
    skipped = 0
    
    for data in VIETNAM_DESTINATIONS:
        try:
            # Tạo hoặc lấy region
            region, _ = Region.objects.get_or_create(
                regionName=data['region']
            )
            
            # Kiểm tra đã tồn tại chưa
            if Destinations.objects.filter(
                desName=data['name'],
                location=data['location']
            ).exists():
                print(f"⏭  Đã tồn tại: {data['name']}")
                skipped += 1
                continue
            
            # Tạo destination mới
            Destinations.objects.create(
                desName=data['name'],
                region=region,
                location=data['location'],
                description=data.get('description', ''),
                category=data.get('category', ''),
                rating=data.get('rating', 0.0),
                address=data.get('address', ''),
                phone=data.get('phone', ''),
                website=data.get('website', ''),
                price_range=data.get('price_range', ''),
                opening_hours=data.get('opening_hours', ''),
                image_url=data.get('image_url', '')
            )
            
            print(f"✓ Đã thêm: {data['name']} - {data['location']} ({data['region']}) - ⭐{data['rating']}")
            created += 1
            
        except Exception as e:
            print(f"❌ Lỗi khi thêm {data['name']}: {e}")
    
    print("\n" + "="*70)
    print("📊 KẾT QUẢ")
    print("="*70)
    print(f"✅ Đã thêm mới:  {created} địa điểm")
    print(f"⏭  Đã bỏ qua:    {skipped} địa điểm (trùng)")
    print(f"📍 Tổng cộng:    {Destinations.objects.count()} địa điểm trong database")
    print("="*70 + "\n")
    print("✅ HOÀN THÀNH!\n")


if __name__ == '__main__':
    import_destinations()
