# Hướng dẫn chuyển từ SQLite sang MySQL

## Bước 1: Cài đặt MySQL Server
- Download và cài MySQL Community Server từ: https://dev.mysql.com/downloads/mysql/
- Hoặc dùng XAMPP/WAMP đã có sẵn MySQL

## Bước 2: Tạo Database
Chạy một trong các cách sau:

**Cách 1: Dùng MySQL Command Line:**
```bash
mysql -u root -p
```
Sau đó chạy:
```sql
CREATE DATABASE smarttravel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

**Cách 2: Dùng file SQL có sẵn:**
```bash
mysql -u root -p < create_mysql_db.sql
```

**Cách 3: Dùng phpMyAdmin** (nếu có XAMPP/WAMP):
- Truy cập http://localhost/phpmyadmin
- Tạo database tên `smarttravel_db`

## Bước 3: Cấu hình kết nối
Cập nhật file `.env` với thông tin MySQL của bạn:
```
DB_NAME=smarttravel_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

## Bước 4: Chạy Migrations
```bash
cd website
python manage.py migrate
```

## Bước 5: Import dữ liệu từ SQLite
```bash
python manage.py loaddata ../data_backup.json
```

## Lưu ý
- File `data_backup.json` đã được tạo từ SQLite cũ
- Nếu lỗi khi import, có thể cần chạy lại `import_data.py`
- Sau khi chuyển xong, có thể xóa file `db.sqlite3` cũ

## Cho Team Members
Khi clone project, chỉ cần:
1. Cài MySQL và tạo database `smarttravel_db`
2. Cấu hình `.env` với thông tin MySQL của mình
3. Chạy `python manage.py migrate`
4. Không cần commit database vào Git nữa!
