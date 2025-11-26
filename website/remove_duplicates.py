import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import Destinations
from django.db.models import Count, Min

def remove_duplicate_destinations():
    """
    Xóa các destinations trùng lặp, giữ lại bản ghi có ID nhỏ nhất
    """
    # Tìm tất cả desName có trùng lặp
    duplicates = Destinations.objects.values('desName').annotate(
        count=Count('id'),
        min_id=Min('id')
    ).filter(count__gt=1, desName__isnull=False)

    total_removed = 0

    for dup in duplicates:
        des_name = dup['desName']
        min_id = dup['min_id']

        # Lấy tất cả bản ghi trùng tên, trừ bản có ID nhỏ nhất
        to_delete = Destinations.objects.filter(desName=des_name).exclude(id=min_id)

        count_deleted = to_delete.count()
        if count_deleted > 0:
            print(f'Deleting {count_deleted} duplicates for "{des_name}" (keeping ID {min_id})')
            to_delete.delete()
            total_removed += count_deleted

    print(f'\nTotal duplicates removed: {total_removed}')
    print(f'Remaining destinations: {Destinations.objects.count()}')

if __name__ == '__main__':
    print('Starting duplicate removal process...')
    remove_duplicate_destinations()
    print('Done!')