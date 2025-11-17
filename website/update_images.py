"""
Script to update image URLs for destinations
Có 2 options:
1. Sử dụng ảnh placeholder từ Unsplash (tự động)
2. Nhập URL thủ công cho từng địa điểm
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Location, Destinations

def option_1_unsplash_placeholder():
    """
    Sử dụng Unsplash với search query tự động
    Ảnh chất lượng cao, miễn phí
    """
    print("\n🖼️  CẬP NHẬT ẢNH TỰ ĐỘNG TỪ UNSPLASH\n")
    
    destinations = Destinations.objects.all()
    updated = 0
    
    for dest in destinations:
        # Tạo search query từ tên địa điểm và location
        location_name = dest.location.locationName if dest.location else "vietnam"
        query = f"{dest.desName} {location_name}".replace(" ", "+")
        
        # Unsplash source URL - tự động random ảnh phù hợp
        # Size: 800x600 pixels
        unsplash_url = f"https://source.unsplash.com/800x600/?{query},vietnam,travel"
        
        dest.image_url = unsplash_url
        dest.save()
        
        updated += 1
        print(f"✅ {dest.desName} → {unsplash_url}")
    
    print(f"\n✅ Đã cập nhật {updated} ảnh từ Unsplash!")
    print("💡 Lưu ý: Ảnh sẽ random mỗi lần reload, nên thay bằng URL cố định sau")

def option_2_picsum_placeholder():
    """
    Sử dụng Picsum - ảnh placeholder đẹp
    Mỗi địa điểm có 1 ảnh unique
    """
    print("\n🖼️  CẬP NHẬT ẢNH PLACEHOLDER TỪ PICSUM\n")
    
    destinations = Destinations.objects.all()
    updated = 0
    
    for dest in destinations:
        # Generate unique seed từ tên để ảnh cố định
        seed = abs(hash(dest.desName)) % 1000
        picsum_url = f"https://picsum.photos/seed/{seed}/800/600"
        
        dest.image_url = picsum_url
        dest.save()
        
        updated += 1
        print(f"✅ {dest.desName} → {picsum_url}")
    
    print(f"\n✅ Đã cập nhật {updated} ảnh từ Picsum!")

def option_3_category_default():
    """
    Sử dụng ảnh mặc định theo category
    Cần tạo ảnh trong Static/images/ trước
    """
    print("\n🖼️  CẬP NHẬT ẢNH MẶC ĐỊNH THEO CATEGORY\n")
    
    category_images = {
        'Museums': '/static/images/museum-default.jpg',
        'Landmarks': '/static/images/landmark-default.jpg',
        'Shrines/Temples': '/static/images/temple-default.jpg',
    }
    
    destinations = Destinations.objects.all()
    updated = 0
    
    for dest in destinations:
        if dest.category in category_images:
            dest.image_url = category_images[dest.category]
            dest.save()
            updated += 1
            print(f"✅ {dest.desName} ({dest.category})")
    
    print(f"\n✅ Đã cập nhật {updated} ảnh theo category!")

def option_4_manual_input():
    """
    Nhập URL thủ công cho các địa điểm quan trọng
    """
    print("\n🖼️  NHẬP URL ẢNH THỦ CÔNG\n")
    print("Các địa điểm hiện tại:\n")
    
    destinations = Destinations.objects.all()[:10]  # Chỉ show 10 đầu
    
    for i, dest in enumerate(destinations, 1):
        print(f"{i}. {dest.desName} ({dest.location.locationName if dest.location else 'Unknown'})")
        print(f"   Current URL: {dest.image_url or 'Chưa có'}\n")
    
    print("Nhập ID địa điểm để cập nhật (hoặc 'q' để thoát):")
    
    while True:
        choice = input("\nID (hoặc 'q'): ").strip()
        
        if choice.lower() == 'q':
            break
        
        try:
            dest_id = int(choice)
            dest = Destinations.objects.get(id=dest_id)
            
            print(f"\nĐịa điểm: {dest.desName}")
            new_url = input("Nhập URL ảnh mới: ").strip()
            
            if new_url:
                dest.image_url = new_url
                dest.save()
                print(f"✅ Đã cập nhật!")
            
        except ValueError:
            print("❌ Vui lòng nhập số!")
        except Destinations.DoesNotExist:
            print("❌ Không tìm thấy địa điểm!")

def main():
    print("="*60)
    print("  CÔNG CỤ CẬP NHẬT ẢNH CHO DESTINATIONS")
    print("="*60)
    
    print("\nChọn phương pháp:")
    print("1. Unsplash - Ảnh tự động theo tên địa điểm (khuyên dùng)")
    print("2. Picsum - Ảnh placeholder đẹp (nhanh)")
    print("3. Category defaults - Ảnh mặc định theo loại")
    print("4. Nhập thủ công - Cho các địa điểm quan trọng")
    print("5. Thoát")
    
    choice = input("\nLựa chọn (1-5): ").strip()
    
    if choice == '1':
        confirm = input("⚠️  Cập nhật TẤT CẢ ảnh bằng Unsplash? (y/n): ")
        if confirm.lower() == 'y':
            option_1_unsplash_placeholder()
    elif choice == '2':
        confirm = input("⚠️  Cập nhật TẤT CẢ ảnh bằng Picsum? (y/n): ")
        if confirm.lower() == 'y':
            option_2_picsum_placeholder()
    elif choice == '3':
        option_3_category_default()
    elif choice == '4':
        option_4_manual_input()
    elif choice == '5':
        print("👋 Tạm biệt!")
    else:
        print("❌ Lựa chọn không hợp lệ!")

if __name__ == '__main__':
    main()
