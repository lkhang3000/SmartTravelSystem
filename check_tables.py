import os
import sys
sys.path.append('D:\\SmartTravel\\website')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
tables = [row[0] for row in cursor.fetchall()]
print('Tables:', tables)