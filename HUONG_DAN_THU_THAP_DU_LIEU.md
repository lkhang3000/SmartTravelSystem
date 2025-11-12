# 🗺️ Hướng Dẫn Thu Thập Dữ Liệu Địa Điểm Du Lịch

## 📋 Tổng quan

Có **3 cách** để thu thập dữ liệu địa điểm du lịch thực:

### 1️⃣ Sử dụng Google Places API (Tự động - Khuyên dùng)
### 2️⃣ Nhập thủ công qua CSV
### 3️⃣ Nhập trực tiếp trong script

---

## 🚀 Cách 1: Sử dụng Google Places API

### Bước 1: Lấy API Key
1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới hoặc chọn project có sẵn
3. Bật **Google Places API**
4. Tạo credentials → API Key
5. Copy API key

### Bước 2: Cài đặt thư viện
```bash
pip install requests
```

### Bước 3: Chạy scraper
```bash
cd d:\SmartTravelSystem\website\sightseeing\Services
python data_scraper.py
```

Chọn option **2** và nhập:
- API key của bạn
- Từ khóa tìm kiếm, ví dụ:
  - `tourist attractions in Hanoi`
  - `things to do in Da Nang`
  - `beaches in Phu Quoc`

### Ưu điểm:
✅ Tự động lấy: tên, địa chỉ, rating, ảnh, giờ mở cửa, website, SĐT
✅ Dữ liệu chính xác từ Google Maps
✅ Nhanh chóng (có thể lấy hàng chục địa điểm trong vài phút)

### Nhược điểm:
⚠️ Cần API key (miễn phí nhưng có giới hạn 300$/tháng credit)
⚠️ Phụ thuộc vào dữ liệu Google

---

## 📝 Cách 2: Nhập từ File CSV

### Bước 1: Tạo file CSV template
```bash
cd d:\SmartTravelSystem\website\sightseeing\Services
python data_scraper.py
```

Chọn option **4** để tạo file `template.csv`

### Bước 2: Điền dữ liệu vào Excel/CSV

Mở `template.csv` bằng Excel và điền thông tin:

| name | location | region | category | rating | description | price_range | address | phone | website | opening_hours | image_url |
|------|----------|--------|----------|--------|-------------|-------------|---------|-------|---------|---------------|-----------|
| Chùa Một Cột | Hà Nội | miền Bắc | Di tích | 4.5 | Ngôi chùa cổ | Miễn phí | Ba Đình, HN | 024... | http://... | 7:00-18:00 | http://... |

### Bước 3: Import vào hệ thống
```bash
python data_scraper.py
```
Chọn option **3** và nhập đường dẫn file CSV

### Ưu điểm:
✅ Không cần API
✅ Có thể nhập hàng loạt
✅ Dễ kiểm soát dữ liệu

### Nhược điểm:
⚠️ Phải tự tìm và nhập thủ công
⚠️ Mất thời gian

---

## ✍️ Cách 3: Nhập Trực Tiếp Trong Script

```bash
cd d:\SmartTravelSystem\website\sightseeing\Services
python data_scraper.py
```

Chọn option **1** và nhập từng trường thông tin

### Ưu điểm:
✅ Nhanh với số lượng ít
✅ Không cần file phụ

### Nhược điểm:
⚠️ Chậm với số lượng lớn

---

## 📊 Nguồn Dữ Liệu Khác (Thu thập thủ công)

### Trang web du lịch Việt Nam:
1. **Vietnam Tourism**: https://vietnam.travel/
2. **TripAdvisor Vietnam**: https://www.tripadvisor.com.vn/
3. **Booking.com**: Phần "Things to do"
4. **Lonely Planet Vietnam**: https://www.lonelyplanet.com/vietnam
5. **Tổng cục Du lịch**: https://www.vietnam.travel/vi

### Cách thu thập:
1. Vào trang web
2. Tìm thông tin địa điểm (tên, mô tả, ảnh...)
3. Copy thông tin vào CSV hoặc nhập trực tiếp

---

## 🎯 Sau Khi Thu Thập Xong

### 1. Kiểm tra dữ liệu
```bash
python data_scraper.py
```
Chọn option **5** để xem danh sách địa điểm

### 2. Lưu dữ liệu
Chọn option **6** để lưu vào `sightseeing_spots.json`

### 3. Tạo migrations cho model mới
```bash
cd d:\SmartTravelSystem\website
python manage.py makemigrations
python manage.py migrate
```

### 4. Load vào database
```bash
python manage.py load_destinations
```

---

## 💡 Gợi Ý Thu Thập

### Địa điểm nên thu thập (Top destinations):

**Miền Bắc:**
- Vịnh Hạ Long, Quảng Ninh
- Phố cổ Hà Nội
- Chùa Hương, Hà Nội
- Ninh Bình (Tràng An, Tam Cốc)

**Tây Bắc:**
- Sa Pa, Lào Cai
- Fansipan
- Mù Cang Chải
- Hà Giang

**Miền Trung:**
- Phố cổ Hội An
- Bà Nà Hills, Đà Nẵng
- Cố đô Huế
- Phong Nha - Kẻ Bàng

**Tây Nguyên:**
- Đà Lạt
- Buôn Ma Thuột
- Pleiku

**Miền Nam:**
- Phú Quốc
- Vũng Tàu
- Mũi Né
- Cần Thơ (chợ nổi)

---

## ❓ Câu Hỏi Thường Gặp

**Q: Google API có miễn phí không?**
A: Có, Google cho $300 credit/tháng (~ 30,000 requests)

**Q: Tôi không có API key thì sao?**
A: Dùng cách 2 hoặc 3 (CSV hoặc nhập tay)

**Q: File JSON ở đâu?**
A: `d:\SmartTravelSystem\website\sightseeing\Services\sightseeing_spots.json`

**Q: Làm sao biết đã load thành công?**
A: Chạy `python manage.py load_destinations` sẽ hiển thị số lượng đã tạo

---

## 📞 Cần Hỗ Trợ?

Mở file này và làm theo từng bước. Nếu gặp lỗi, kiểm tra:
1. ✅ Đã cài pip install requests
2. ✅ Đã chạy migrations
3. ✅ File JSON có đúng định dạng
4. ✅ Database đã được tạo
