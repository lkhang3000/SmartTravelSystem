# 🗺️ Hệ Thống Thu Thập Dữ Liệu Địa Điểm Du Lịch

## 📊 Tổng Quan

Bạn có **2 cách đơn giản** để thu thập dữ liệu địa điểm du lịch:

| Phương pháp | Số lượng | Độ khó | API Key | Thời gian |
|-------------|----------|--------|---------|-----------|
| **1. Import dữ liệu có sẵn** | ~20 | ⭐ Dễ | ❌ Không | 1 phút |
| **2. OpenStreetMap API** | 50-100 | ⭐⭐ Trung bình | ❌ Không | 3-5 phút |

---

## 🚀 PHƯƠNG ÁN 1: Import Dữ Liệu Có Sẵn (Khuyên dùng)

### ✅ Tại sao nên dùng?
- ⚡ **Nhanh nhất** - chỉ 1 phút
- 📊 **21 địa điểm** nổi tiếng nhất Việt Nam
- ✅ Dữ liệu **đầy đủ**: rating, giá vé, giờ mở cửa, SĐT, website
- 🎯 Bao gồm: Vịnh Hạ Long, Phố Cổ Hội An, Bà Nà Hills, Phú Quốc...

### 📝 Cách Sử Dụng:

```cmd
cd d:\SmartTravelSystem\website
python import_real_data.py
```

### 📍 Danh Sách 21 Địa Điểm:

**Miền Bắc (5):**
- Vịnh Hạ Long ⭐4.9
- Hoàng Thành Thăng Long ⭐4.5
- Chùa Một Cột ⭐4.3
- Hồ Hoàn Kiếm ⭐4.6
- Tràng An ⭐4.8

**Tây Bắc (2):**
- Fansipan ⭐4.9
- Bản Cát Cát ⭐4.5

**Miền Trung (6):**
- Phố Cổ Hội An ⭐4.8
- Bà Nà Hills ⭐4.7
- Bãi Biển Mỹ Khê ⭐4.8
- Cố đô Huế ⭐4.7
- Động Phong Nha ⭐4.9
- Bãi Dài Nha Trang ⭐4.7

**Tây Nguyên (2):**
- Hồ Xuân Hương ⭐4.6
- Thác Datanla ⭐4.5

**Miền Nam (4):**
- Dinh Độc Lập ⭐4.6
- Nhà thờ Đức Bà ⭐4.5
- Bãi Sao Phú Quốc ⭐4.9
- Chợ Nổi Cái Răng ⭐4.7

---

## 🗺️ PHƯƠNG ÁN 2: OpenStreetMap (Thêm Nhiều Địa Điểm)

### ✅ Tại sao dùng OpenStreetMap?
- 🌍 **Miễn phí 100%**, không cần API key
- 📊 Có thể lấy thêm **50-100 địa điểm**
- 🇻🇳 Dữ liệu từ cộng đồng toàn cầu

### ⚠️ Lưu Ý:
- Có thể bị **timeout** nếu server quá tải
- Dữ liệu **ít chi tiết** hơn import_real_data
- Mất **3-5 phút** để chạy

### 📝 Cách Sử Dụng:

```cmd
cd d:\SmartTravelSystem\website
python simple_osm_upload.py
```

Script sẽ tự động:
1. Tìm kiếm địa điểm du lịch tại: Hà Nội, Đà Nẵng, TP.HCM, Quảng Ninh, Lâm Đồng, Sa Pa
2. Lấy thông tin: tên, địa chỉ, loại hình
3. Tự động phân loại theo miền
4. Upload vào database
5. Bỏ qua địa điểm trùng lặp

---

## 🎯 KẾ HOẠCH KHUYÊN DÙNG

### Lộ trình nhanh (2 phút):
```cmd
# Bước 1: Import 21 địa điểm có sẵn
python import_real_data.py
```
→ ✅ **Hoàn thành!** Có ngay 21 địa điểm nổi tiếng

### Nếu muốn thêm địa điểm (5 phút):
```cmd
# Bước 2: Thử OpenStreetMap
python simple_osm_upload.py
```
→ ✅ Thêm 50-100 địa điểm nữa (nếu không timeout)

### Kết quả cuối cùng:
- **21-120 địa điểm** du lịch Việt Nam
- Dữ liệu đầy đủ, sẵn sàng sử dụng

---

## 📊 Kiểm Tra Dữ Liệu

### Cách 1: Django Shell
```cmd
python manage.py shell
```

```python
from sightseeing.models import Destinations, Region

print(f"Tổng số địa điểm: {Destinations.objects.count()}")
print(f"Tổng số miền: {Region.objects.count()}")

# Xem theo miền
for region in Region.objects.all():
    count = region.destinations.count()
    print(f"{region.regionName}: {count} địa điểm")

# Xem 10 địa điểm đầu
for d in Destinations.objects.all()[:10]:
    print(f"⭐{d.rating} - {d.desName} ({d.location})")
```

### Cách 2: Django Admin
```cmd
python manage.py createsuperuser
python manage.py runserver
```
Truy cập: http://localhost:8000/admin

---

## 📁 Cấu Trúc Files

```
website/
├── import_real_data.py       # ⭐ Script chính - 21 địa điểm
├── simple_osm_upload.py      # OpenStreetMap scraper
└── sightseeing/
    ├── models.py             # Model Destinations và Region
    ├── Services/
    │   └── osm_scraper.py    # OpenStreetMap logic
    └── management/
        └── commands/
            ├── load_destinations.py  # Load từ JSON
            └── assign_regions.py     # Gán region tự động
```

---

## 🔄 Thêm Dữ Liệu Thủ Công

Nếu muốn thêm địa điểm thủ công, dùng Django Admin:

```cmd
python manage.py createsuperuser
python manage.py runserver
```

Truy cập: http://localhost:8000/admin/sightseeing/destinations/add/

---

## ❓ Câu Hỏi Thường Gặp

**Q: Tôi nên dùng phương pháp nào?**  
A: Dùng **import_real_data.py** - nhanh, đơn giản, dữ liệu chất lượng cao.

**Q: Mất bao lâu?**  
A: 1 phút với import_real_data, 3-5 phút với OpenStreetMap.

**Q: Có cần API key không?**  
A: **Không!** Cả 2 phương pháp đều miễn phí, không cần key.

**Q: Dữ liệu có ảnh không?**  
A: import_real_data có một số ảnh. OpenStreetMap ít ảnh hơn.

**Q: Có thể chạy lại không?**  
A: Có! Script tự động bỏ qua địa điểm trùng lặp.

**Q: OpenStreetMap timeout thì sao?**  
A: Dùng import_real_data là đủ. Hoặc thử lại sau vài phút.

---

## 🆘 Xử Lý Lỗi

### Lỗi: ModuleNotFoundError
```cmd
pip install requests
```

### Lỗi: No module named 'sightseeing'
```cmd
cd d:\SmartTravelSystem\website
# Đảm bảo đang ở đúng thư mục
```

### Lỗi: Migration
```cmd
python manage.py makemigrations
python manage.py migrate
```

### OpenStreetMap Timeout
→ Đây là lỗi server bên ngoài, không phải lỗi code
→ Giải pháp: Dùng **import_real_data.py** thay thế

---

## 🎉 Kết Luận

**Khuyên dùng cho bạn:**

```cmd
# Chạy lệnh này là đủ!
cd d:\SmartTravelSystem\website
python import_real_data.py
```

**🎯 Kết quả: 21 địa điểm du lịch nổi tiếng Việt Nam!**

Nếu muốn thêm nữa, thử:
```cmd
python simple_osm_upload.py
```

---

Made with ❤️ for Smart Travel System

| Phương pháp | Số lượng | Độ khó | API Key | Chi phí |
|-------------|----------|--------|---------|---------|
| **1. Import dữ liệu có sẵn** | ~20 | ⭐ Dễ | ❌ Không | ✅ Miễn phí |
| **2. Goong Maps API** | 100-300 | ⭐⭐ Trung bình | ✅ Cần | ✅ Miễn phí |
| **3. OpenStreetMap** | 50-200 | ⭐⭐⭐ Khó | ❌ Không | ✅ Miễn phí |

---

## 🚀 KHUYÊN DÙNG: Goong Maps API

### ✅ Tại sao nên dùng Goong?
- 🇻🇳 Dữ liệu Việt Nam chính xác nhất
- 💰 Miễn phí 5,000 requests/ngày
- 📸 Có ảnh, rating, giờ mở cửa, SĐT, website
- 🔄 Tự động phân loại miền và category
- ⚡ Nhanh và ổn định

### 📝 Cách Sử Dụng:

#### Bước 1: Lấy API Key (2 phút)
1. Truy cập: https://account.goong.io/
2. Đăng ký tài khoản miễn phí
3. Tạo API Key
4. Copy key

#### Bước 2: Test API (1 phút)
```cmd
cd d:\SmartTravelSystem\website
python test_goong_api.py
```
Nhập API key khi được hỏi.

#### Bước 3: Cào Dữ Liệu (5-10 phút)
```cmd
python goong_scraper.py
```
Nhập API key và chờ script chạy.

### 📖 Hướng dẫn chi tiết:
Xem file: `HUONG_DAN_GOONG_API.md`

---

## 💾 Phương Án 1: Import Dữ Liệu Có Sẵn

**Nếu bạn muốn nhanh và không cần nhiều dữ liệu:**

```cmd
cd d:\SmartTravelSystem\website
python import_real_data.py
```

### ✅ Kết quả:
- 21 địa điểm du lịch nổi tiếng
- Dữ liệu đầy đủ: rating, giờ mở cửa, giá vé...
- Bao gồm: Vịnh Hạ Long, Phố Cổ Hội An, Bà Nà Hills, Phú Quốc...

---

## 🗺️ Phương Án 3: OpenStreetMap

**Nếu Goong API không hoạt động:**

```cmd
python sightseeing\Services\osm_scraper.py
```

### ⚠️ Lưu ý:
- Có thể bị timeout do server quá tải
- Dữ liệu ít chi tiết hơn Goong
- Không cần API key

---

## 📊 Kiểm Tra Dữ Liệu

### Xem số lượng trong database:
```cmd
python manage.py shell
```

Trong shell:
```python
from sightseeing.models import Destinations, Region

print(f"Tổng số địa điểm: {Destinations.objects.count()}")
print(f"Tổng số miền: {Region.objects.count()}")

# Xem theo miền
for region in Region.objects.all():
    count = region.destinations.count()
    print(f"{region.regionName}: {count} địa điểm")
```

### Hoặc dùng Django Admin:
```cmd
python manage.py createsuperuser
python manage.py runserver
```
Truy cập: http://localhost:8000/admin

---

## 🔄 Cập Nhật Dữ Liệu

Bạn có thể chạy lại các script bất cứ lúc nào:
- Script tự động **bỏ qua địa điểm trùng**
- Chỉ thêm địa điểm mới

```cmd
# Chạy lại để thêm dữ liệu mới
python goong_scraper.py
```

---

## 📁 Cấu Trúc Files

```
website/
├── goong_scraper.py          # ⭐ Script chính - Goong API
├── test_goong_api.py         # Test Goong API
├── import_real_data.py       # Import 21 địa điểm có sẵn
├── simple_osm_upload.py      # OpenStreetMap scraper
└── sightseeing/
    ├── models.py             # Model Destinations và Region
    └── management/
        └── commands/
            ├── load_destinations.py  # Load từ JSON
            └── assign_regions.py     # Gán region tự động

Docs/
├── HUONG_DAN_GOONG_API.md    # Hướng dẫn Goong chi tiết
└── HUONG_DAN_THU_THAP_DU_LIEU.md  # Hướng dẫn tổng hợp
```

---

## 🎯 Kế Hoạch Khuyên Dùng

### Lộ trình nhanh (15 phút):
1. ✅ Chạy `import_real_data.py` → 21 địa điểm
2. ✅ Lấy Goong API key (2 phút)
3. ✅ Chạy `goong_scraper.py` → +100-300 địa điểm
4. ✅ **Tổng cộng: 120-320 địa điểm** 🎉

### Nếu có nhiều thời gian:
- Tùy chỉnh queries trong `goong_scraper.py`
- Thêm nhiều từ khóa tìm kiếm
- Chạy nhiều lần với các vùng khác nhau

---

## ❓ Câu Hỏi Thường Gặp

**Q: Goong API có miễn phí không?**  
A: Có! Miễn phí 5,000 requests/ngày, không cần thẻ tín dụng.

**Q: Tôi nên dùng phương pháp nào?**  
A: Dùng **Goong Maps** để có nhiều dữ liệu chính xác nhất.

**Q: Mất bao lâu để cào dữ liệu?**  
A: 5-10 phút với Goong API (tùy số lượng queries).

**Q: Dữ liệu có ảnh không?**  
A: Có! Goong API cung cấp link ảnh của địa điểm.

**Q: Làm sao biết đã thành công?**  
A: Script sẽ hiển thị thống kê cuối cùng với số lượng đã thêm.

---

## 🆘 Hỗ Trợ

Nếu gặp lỗi, kiểm tra:
1. ✅ Đã chạy migrations: `python manage.py migrate`
2. ✅ Đã cài requests: `pip install requests`
3. ✅ API key đúng (nếu dùng Goong)
4. ✅ Có kết nối internet

---

## 🎉 Kết Luận

**Bước tiếp theo của bạn:**

```cmd
# Bước 1: Import dữ liệu nền
python import_real_data.py

# Bước 2: Lấy Goong API key
# Truy cập: https://account.goong.io/

# Bước 3: Test API
python test_goong_api.py

# Bước 4: Cào dữ liệu chính
python goong_scraper.py
```

**🎯 Mục tiêu: 100-300 địa điểm du lịch Việt Nam trong database!**

---

Made with ❤️ for Smart Travel System
