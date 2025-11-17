"""
recommender.py
---------------
This module reads sightseeing spot data from a JSON file,
filters it based on user preferences, and outputs recommended
spots into a new JSON file.
"""

import json
import os
from typing import List, Dict



# Data Model

class SightseeingSpot:
    def __init__(self, name: str, location: str, category: str, rating: float, region: str = None):
        self.name = name
        self.location = location
        self.category = category
        self.rating = rating
        # Keep region for backward compatibility but use location for filtering

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "location": self.location,
            "category": self.category,
            "rating": self.rating
        }
# Recommender System
class SightseeingRecommender:
    def __init__(self, spots_file: str, users_file: str):
        self.spots_file = spots_file
        self.users_file = users_file
        self.spots = self.load_spots()
        self.users = self.load_users()

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

    def recommend_for_user(self, user_data: Dict) -> Dict:
        """Filter and recommend one best spot for a user."""

        preferences = user_data["trip_preferences"]
        location = preferences["domestic_or_international"].get("location", "").lower()
        tags = [t.lower() for t in preferences.get("tags", [])]
        budget = preferences.get("budget", 0)

        filtered = self.spots

        # Lọc theo thành phố/location
        if location:
            filtered = [spot for spot in filtered if location in spot.location.lower()] or filtered

        # Lọc theo tags (VD: biển, núi, thiên nhiên, thư giãn...)
        if tags:
            filtered = [
                spot for spot in filtered
                if any(tag in spot.category.lower() or tag in spot.name.lower() for tag in tags)
            ] or filtered

        # Sắp xếp theo rating
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