import os
import csv
from datetime import datetime
from django.conf import settings

def generate_search_history_csv():
    """
    Generate search history CSV file for recommender system
    Returns the file path of the generated CSV
    """
    from ..models import SearchHistory

    # Create Services directory if it doesn't exist
    services_dir = os.path.join(settings.BASE_DIR, 'sightseeing', 'Services')
    os.makedirs(services_dir, exist_ok=True)

    # CSV file path
    csv_file_path = os.path.join(services_dir, 'search_history.csv')

    # Write CSV file
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['user_id', 'destination_id', 'rating', 'timestamp'])

        # Write data
        search_history = SearchHistory.objects.all().order_by('timestamp')
        for entry in search_history:
            writer.writerow([
                entry.user_id,
                entry.destination_id,
                entry.rating,
                entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])

    print(f"Generated search history CSV at: {csv_file_path}")
    return csv_file_path

def get_search_history_csv_path():
    """
    Get the path to the search history CSV file
    """
    services_dir = os.path.join(settings.BASE_DIR, 'sightseeing', 'Services')
    return os.path.join(services_dir, 'search_history.csv')

def load_search_history_from_csv():
    """
    Load search history data from CSV file for recommender system
    Returns list of dictionaries with search history data
    """
    csv_path = get_search_history_csv_path()

    if not os.path.exists(csv_path):
        print(f"Search history CSV not found at: {csv_path}")
        return []

    search_history = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            search_history.append({
                'user_id': row['user_id'],
                'destination_id': row['destination_id'],
                'rating': float(row['rating']),
                'timestamp': datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            })

    return search_history