"""
Script chuyển dữ liệu từ SQLite sang MySQL
"""
import sqlite3
import mysql.connector
from decouple import config

# Connect to SQLite
print("📚 Kết nối SQLite...")
sqlite_conn = sqlite3.connect('website/db.sqlite3')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Connect to MySQL
print("🔄 Kết nối MySQL...")
mysql_conn = mysql.connector.connect(
    host=config('DB_HOST', default='localhost'),
    user=config('DB_USER', default='root'),
    password=config('DB_PASSWORD', default=''),
    database=config('DB_NAME', default='smarttravel_db'),
    port=int(config('DB_PORT', default='3306')),
    charset='utf8mb4'
)
mysql_cursor = mysql_conn.cursor()

print("✅ Kết nối thành công!\n")

# Tắt foreign key checks tạm thời
mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

# Tables to migrate (theo thứ tự phụ thuộc)
tables_to_migrate = [
    'auth_user',
    'sightseeing_location',
    'sightseeing_destinations',
    'sightseeing_hotel',
    'sightseeing_usersprofile',
    'sightseeing_trip',
    'sightseeing_tripitem',
    'sightseeing_searchhistory',
    'sightseeing_comment',
]

total_migrated = 0

for table_name in tables_to_migrate:
    try:
        # Lấy dữ liệu từ SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"⚠️  {table_name}: Không có dữ liệu")
            continue
            
        # Lấy tên columns
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Clear bảng MySQL trước
        mysql_cursor.execute(f"DELETE FROM {table_name}")
        
        # Insert từng row
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        migrated_count = 0
        for row in rows:
            try:
                mysql_cursor.execute(insert_query, tuple(row))
                migrated_count += 1
            except Exception as e:
                print(f"   ⚠️  Lỗi insert row: {e}")
                continue
        
        mysql_conn.commit()
        total_migrated += migrated_count
        print(f"✅ {table_name}: {migrated_count} records")
        
    except Exception as e:
        print(f"❌ {table_name}: Lỗi - {e}")

# Bật lại foreign key checks
mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
mysql_conn.commit()

# Đóng kết nối
sqlite_conn.close()
mysql_conn.close()

print(f"\n🎉 HOÀN TẤT! Đã chuyển tổng cộng {total_migrated} records sang MySQL!")
print("🚀 Chạy: cd website && python manage.py runserver")
