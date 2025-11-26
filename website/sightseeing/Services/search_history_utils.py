import os
import csv
from datetime import datetime
from django.conf import settings

def calculate_user_preference_score(user, destination):
    """
    Calculate user preference score for a destination based on user actions
    Returns a score from 0-5 scale where:
    - Added to trip list: 5.0 (highest)
    - Commented: 3.5 (interested)
    - Both actions: 5.0 (maximum preference)
    """
    from ..models import TripItem, Comment
    
    score = 0.0
    
    # Check if user added destination to trip list
    added_to_list = TripItem.objects.filter(user=user, destination=destination).exists()
    
    # Check if user commented on destination
    commented = Comment.objects.filter(user=user, destination=destination).exists()
    
    if added_to_list and commented:
        # Both actions - maximum preference
        score = 5.0
    elif added_to_list:
        # Only added to list - high preference
        score = 5.0
    elif commented:
        # Only commented - moderate preference
        score = 3.5
    else:
        # No action - neutral/low preference
        score = 0.0
    
    return score

def update_user_preference_score(user, destination):
    """
    Update or create search history entry with calculated preference score
    """
    from ..models import SearchHistory, UsersProfile
    
    try:
        # Get user profile to get custom user ID
        user_profile = UsersProfile.objects.get(user=user)
        user_id = user_profile.custom_user_id
        
        # Calculate preference score
        score = calculate_user_preference_score(user, destination)
        
        # Remove any existing entries for this user-destination pair to avoid duplicates
        SearchHistory.objects.filter(
            user_id=user_id,
            destination_id=destination.destination_id
        ).delete()
        
        # Create new search history entry
        search_history = SearchHistory.objects.create(
            user_id=user_id,
            destination_id=destination.destination_id,
            score=score,
            timestamp=datetime.now()
        )
        
        # Regenerate CSV after updating score
        generate_search_history_csv()
        
        return search_history, True
        
    except UsersProfile.DoesNotExist:
        # Skip if user profile doesn't exist
        return None, False

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
        writer.writerow(['user_id', 'destination_id', 'score', 'timestamp'])

        # Write data
        search_history = SearchHistory.objects.all().order_by('timestamp')
        for entry in search_history:
            writer.writerow([
                entry.user_id,
                entry.destination_id,
                entry.score,
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
                'score': float(row['score']),
                'timestamp': datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            })

    return search_history