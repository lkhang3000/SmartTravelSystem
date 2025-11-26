"""
recommender.py
---------------
This module reads sightseeing spot data from a JSON file,
filters it based on user preferences, and outputs recommended
spots into a new JSON file. Now also uses search history CSV
for improved recommendations.
"""

import json
import os
import csv
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict



# Data Model

class SightseeingSpot:
    def __init__(self, name: str, location: str, category: str, rating: float, region: str):
        self.name = name
        self.location = location
        self.category = category
        self.rating = rating
        self.region = region  # Miền Bắc / Trung / Nam

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "location": self.location,
            "category": self.category,
            "rating": self.rating,
            "region": self.region
        }

class SearchHistoryEntry:
    def __init__(self, user_id: str, destination_id: str, rating: float, timestamp: datetime):
        self.user_id = user_id
        self.destination_id = destination_id
        self.rating = rating
        self.timestamp = timestamp

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "destination_id": self.destination_id,
            "rating": self.rating,
            "timestamp": self.timestamp.isoformat()
        }
# Recommender System
class SightseeingRecommender:
    def __init__(self, spots_file: str, users_file: str, search_history_file: str = None):
        self.spots_file = spots_file
        self.users_file = users_file
        self.search_history_file = search_history_file or os.path.join(os.path.dirname(__file__), 'search_history.csv')
        self.spots = self.load_spots()
        self.users = self.load_users()
        self.search_history = self.load_search_history()

    def load_spots(self) -> List[SightseeingSpot]:
        """Đọc file địa điểm du lịch"""
        with open(self.spots_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # đảm bảo data có key "locations"
            if "locations" in data:
                data = data["locations"]
            return [SightseeingSpot(**spot) for spot in data]

    def load_users(self) -> List[Dict]:
        """Đọc file người dùng"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("users", [])

    def load_search_history(self) -> List[SearchHistoryEntry]:
        """Load search history from CSV file"""
        search_history = []

        if not os.path.exists(self.search_history_file):
            print(f"Search history file not found: {self.search_history_file}")
            return search_history

        try:
            with open(self.search_history_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                        entry = SearchHistoryEntry(
                            user_id=row['user_id'],
                            destination_id=row['destination_id'],
                            rating=float(row['rating']),
                            timestamp=timestamp
                        )
                        search_history.append(entry)
                    except (ValueError, KeyError) as e:
                        print(f"Error parsing search history row: {row}, Error: {e}")
                        continue
        except Exception as e:
            print(f"Error loading search history: {e}")

        print(f"Loaded {len(search_history)} search history entries")
        return search_history

    def get_user_search_history(self, user_id: str) -> List[SearchHistoryEntry]:
        """Get search history for a specific user"""
        return [entry for entry in self.search_history if entry.user_id == user_id]

    def get_popular_destinations(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get most popular destinations based on search history ratings"""
        destination_ratings = defaultdict(list)

        for entry in self.search_history:
            destination_ratings[entry.destination_id].append(entry.rating)

        # Calculate average rating for each destination
        avg_ratings = []
        for dest_id, ratings in destination_ratings.items():
            avg_rating = sum(ratings) / len(ratings)
            avg_ratings.append((dest_id, avg_rating))

        # Sort by average rating (descending) and return top limit
        avg_ratings.sort(key=lambda x: x[1], reverse=True)
        return avg_ratings[:limit]

    def get_similar_users(self, user_id: str, limit: int = 5) -> List[str]:
        """Find users with similar search patterns"""
        user_history = self.get_user_search_history(user_id)
        if not user_history:
            return []

        user_destinations = set(entry.destination_id for entry in user_history)

        similar_users = []
        for entry in self.search_history:
            if entry.user_id != user_id:
                other_user_destinations = set(e.destination_id for e in self.get_user_search_history(entry.user_id))
                similarity = len(user_destinations.intersection(other_user_destinations)) / len(user_destinations.union(other_user_destinations))
                similar_users.append((entry.user_id, similarity))

        # Remove duplicates and sort by similarity
        similar_users = list(set(similar_users))
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return [user for user, _ in similar_users[:limit]]

    def recommend_for_user(self, user_data: Dict) -> Dict:
        """Filter and recommend one best spot for a user."""

        preferences = user_data["trip_preferences"]
        region = preferences["domestic_or_international"].get("region", "").lower()
        tags = [t.lower() for t in preferences.get("tags", [])]
        budget = preferences.get("budget", 0)

        filtered = self.spots

        # Lọc theo vùng
        if region:
            filtered = [spot for spot in filtered if spot.region.lower() == region] or filtered

        # Lọc theo tags (VD: biển, núi, thiên nhiên, thư giãn...)
        if tags:
            filtered = [
                spot for spot in filtered
                if any(tag in spot.category.lower() or tag in spot.name.lower() for tag in tags)
            ] or filtered

        # Giả sử chi phí cao hơn = rating cao hơn, người có budget cao sẽ chọn rating cao
        filtered.sort(key=lambda s: s.rating, reverse=True)

        if not filtered:
            return {}

        best_spot = filtered[0]
        return {
            "username": user_data["user_info"]["username"],
            "recommended_spot": best_spot.to_dict()
        }

    def generate_recommendations(self, users_file: str, output_folder: str = "recommendations"):
        """Generate a JSON file for each user."""
        os.makedirs(output_folder, exist_ok=True)

        with open(users_file, 'r', encoding='utf-8') as file:
            users_data = json.load(file)["users"]
        
        for user in users_data:
            result = self.recommend_for_user(user)
            username = result["username"]
            output_path = os.path.join(output_folder, f"recommend_{username}.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

            print(f"✅ Recommendation saved for {username}: {output_path}")

# 
# Example run
# 
if __name__ == "__main__":
     recommender = SightseeingRecommender("sightseeing_spots.json", "user_data.json")
     recommender.generate_recommendations("user_data.json")