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

    def recommend_for_user(self, user_data: Dict, top_k: int = 5) -> Dict:
        """Gợi ý top K địa điểm thay vì chỉ 1"""

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

        # Tính điểm relevance cho mỗi spot
        scored_spots = []
        for spot in filtered:
            score = self.calculate_relevance_score(spot, user_data)
            scored_spots.append((spot, score))

        # Sắp xếp theo điểm số và lấy top K
        scored_spots.sort(key=lambda x: x[1], reverse=True)
        top_spots = scored_spots[:top_k]

        return {
            "username": user_data["user_info"]["username"],
            "recommendations": [
                {
                    "spot": spot.to_dict(),
                    "relevance_score": round(score, 2)
                }
                for spot, score in top_spots
            ]
        }

    def calculate_relevance_score(self, spot: SightseeingSpot, user_data: Dict) -> float:
        """Tính điểm relevance giữa spot và user preferences"""
        score = 0.0

        preferences = user_data["trip_preferences"]
        tags = [t.lower() for t in preferences.get("tags", [])]
        budget = preferences.get("budget", 0)

        # 1. Điểm từ rating (40% trọng số)
        score += spot.rating * 0.4  # Rating 4.8 -> 1.92 điểm

        # 2. Điểm từ category match (30% trọng số)
        category_match = any(tag in spot.category.lower() for tag in tags)
        name_match = any(tag in spot.name.lower() for tag in tags)

        if category_match or name_match:
            score += 3.0 * 0.3  # Max 0.9 điểm

        # 3. Điểm từ region match (20% trọng số)
        user_region = preferences["domestic_or_international"].get("region", "").lower()
        if user_region and spot.region.lower() == user_region:
            score += 2.0 * 0.2  # 0.4 điểm

        # 4. Điểm từ budget compatibility (10% trọng số)
        # Giả sử budget cao hơn thì ưu tiên địa điểm premium
        budget_score = min(budget / 10000000, 1.0) * 1.0 * 0.1  # Max 0.1 điểm
        score += budget_score

        return score

    def generate_recommendations(self, users_file: str, output_folder: str = "recommendations", top_k: int = 5):
        """Generate a JSON file for each user with top K recommendations."""
        os.makedirs(output_folder, exist_ok=True)

        with open(users_file, 'r', encoding='utf-8') as file:
            users_data = json.load(file)["users"]
        
        for user in users_data:
            result = self.recommend_for_user(user, top_k=top_k)
            username = result["username"]
            output_path = os.path.join(output_folder, f"recommend_{username}.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

            print(f"✅ Top {top_k} recommendations saved for {username}: {output_path}")

# 
# Example run
# 
if __name__ == "__main__":
     recommender = SightseeingRecommender("sightseeing_spots.json", "user_data.json")
     recommender.generate_recommendations("user_data.json", top_k=5)