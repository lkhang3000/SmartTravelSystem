"""
recommender.py
---------------
Collaborative Filtering Item-to-Item Recommender System for Travel Destinations
Based on YouTube tutorial: https://www.youtube.com/watch?v=3ecNC-So0r4
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import SearchHistory, Destinations, UsersProfile

def cosine_similarity_matrix(matrix: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity matrix without scikit-learn"""
    # Normalize each row (vector)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1
    normalized_matrix = matrix / norms

    # Calculate cosine similarity
    similarity = np.dot(normalized_matrix, normalized_matrix.T)

    return similarity

class CollaborativeRecommender:
    def __init__(self):
        self.user_item_matrix = None
        self.item_similarity_df = None
        self.destinations_df = None
        self._load_data()
        self._build_similarity_matrix()

    def _load_data(self):
        """Load data from SearchHistory model instead of CSV"""
        from ..models import SearchHistory
        
        try:
            # Load search history data from database
            search_history_entries = SearchHistory.objects.all().values('user_id', 'destination_id', 'score')
            if search_history_entries:
                search_df = pd.DataFrame(list(search_history_entries))
                print(f"Loaded {len(search_df)} search history records from database")

                # Convert destination_id to proper format (dest_XXX)
                search_df['destination_id'] = search_df['destination_id'].astype(str)
                search_df['destination_id'] = search_df['destination_id'].apply(
                    lambda x: f"dest_{int(x):03d}" if x.isdigit() else x
                )

                # Create user-item matrix
                self.user_item_matrix = search_df.pivot_table(
                    index='user_id',
                    columns='destination_id',
                    values='score',
                    fill_value=0
                )

                print(f"User-item matrix shape: {self.user_item_matrix.shape}")
                print(f"Total ratings: {(self.user_item_matrix > 0).sum().sum()}")
            else:
                print("No search history data in database")
                self.user_item_matrix = pd.DataFrame()

            # Load destinations info from database
            destinations = Destinations.objects.all().values('destination_id', 'desName', 'category', 'rating', 'location')
            self.destinations_df = pd.DataFrame(list(destinations))
            self.destinations_df.set_index('destination_id', inplace=True)

            print(f"Loaded {len(self.destinations_df)} destinations from database")

        except Exception as e:
            print(f"Error loading data: {e}")
            self.destinations_df = pd.DataFrame()
            self.user_item_matrix = pd.DataFrame()



    def _standardize_ratings(self, matrix: pd.DataFrame) -> pd.DataFrame:
        """Standardize ratings by subtracting user mean and dividing by range"""
        # Calculate user means (excluding zeros)
        user_means = {}
        user_ranges = {}

        for user_id in matrix.index:
            user_ratings = matrix.loc[user_id]
            non_zero_ratings = user_ratings[user_ratings > 0]

            if len(non_zero_ratings) > 0:
                user_mean = non_zero_ratings.mean()
                user_range = non_zero_ratings.max() - non_zero_ratings.min()

                # Avoid division by zero
                if user_range == 0:
                    user_range = 1

                user_means[user_id] = user_mean
                user_ranges[user_id] = user_range
            else:
                user_means[user_id] = 0
                user_ranges[user_id] = 1

        # Standardize each rating
        standardized_matrix = matrix.copy()

        for user_id in matrix.index:
            for dest_id in matrix.columns:
                rating = matrix.loc[user_id, dest_id]
                if rating > 0:  # Only standardize actual ratings
                    standardized_rating = (rating - user_means[user_id]) / user_ranges[user_id]
                    standardized_matrix.loc[user_id, dest_id] = standardized_rating

        return standardized_matrix

    def _build_similarity_matrix(self):
        """Build item-to-item similarity matrix using cosine similarity"""
        if self.user_item_matrix.empty:
            print("No user-item data available for similarity calculation")
            self.item_similarity_df = pd.DataFrame()
            return

        # Transpose to get item-user matrix for item-to-item similarity
        item_user_matrix = self.user_item_matrix.T

        # Convert to numpy array
        matrix = item_user_matrix.values

        # Calculate cosine similarity between items
        similarity_matrix = cosine_similarity_matrix(matrix)

        # Convert back to DataFrame
        self.item_similarity_df = pd.DataFrame(
            similarity_matrix,
            index=item_user_matrix.index,
            columns=item_user_matrix.index
        )

        print(f"Built item similarity matrix with shape: {self.item_similarity_df.shape}")
        print(f"Available destinations: {len(self.destinations_df)}")
        print(f"Users with ratings: {len(self.user_item_matrix)}")

    def get_similar_destinations(self, destination_id: str, user_rating: float, top_n: int = 10) -> pd.DataFrame:
        """Get similar destinations based on collaborative filtering similarity"""
        if self.item_similarity_df is None or self.item_similarity_df.empty:
            # Fallback to category/location based similarity if no collaborative data
            return self._get_similar_by_category_location(destination_id, user_rating, top_n)

        if destination_id not in self.item_similarity_df.index:
            print(f"Destination {destination_id} not found in similarity matrix")
            return self._get_similar_by_category_location(destination_id, user_rating, top_n)

        # Get similarity scores for this destination
        similarities = self.item_similarity_df.loc[destination_id]

        # Sort by similarity score (excluding self)
        similar_items = similarities.drop(destination_id).sort_values(ascending=False)

        # Get top similar destinations
        similar_dests = []
        for dest_id, similarity_score in similar_items.head(top_n).items():
            if dest_id in self.destinations_df.index:
                dest_info = self.destinations_df.loc[dest_id]
                # Weight by user rating
                weighted_score = similarity_score * (user_rating / 5.0)
                similar_dests.append({
                    'destination_id': dest_id,
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'similarity_score': weighted_score
                })

        return pd.DataFrame(similar_dests)

    def _get_similar_by_category_location(self, destination_id: str, user_rating: float, top_n: int = 10) -> pd.DataFrame:
        """Fallback method: Get similar destinations based on category and location"""
        if destination_id not in self.destinations_df.index:
            print(f"Destination {destination_id} not found")
            return pd.DataFrame()

        # Get current destination info
        current_dest = self.destinations_df.loc[destination_id]

        # Find destinations with same category or location
        similar_dests = []
        for dest_id, dest_info in self.destinations_df.iterrows():
            if dest_id == destination_id:
                continue

            # Calculate similarity score based on category and location match
            similarity_score = 0.0

            # Same category = high similarity
            if dest_info['category'] == current_dest['category']:
                similarity_score += 0.7

            # Same location = high similarity
            if dest_info.get('location') == current_dest.get('location'):
                similarity_score += 0.5

            # If both match, even higher
            if (dest_info['category'] == current_dest['category'] and
                dest_info.get('location') == current_dest.get('location')):
                similarity_score += 0.3

            if similarity_score > 0:
                # Weight by user rating (higher rating = more weight for similar items)
                weighted_score = similarity_score * (user_rating / 5.0)
                similar_dests.append({
                    'destination_id': dest_id,
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'similarity_score': weighted_score
                })

        # Sort by similarity score and return top_n
        similar_dests.sort(key=lambda x: x['similarity_score'], reverse=True)
        return pd.DataFrame(similar_dests[:top_n])

    def recommend_for_user(self, user_id: str, top_n: int = 10) -> pd.DataFrame:
        """Recommend destinations based on user's high-rated destinations"""
        if self.user_item_matrix is None or user_id not in self.user_item_matrix.index:
            print(f"User {user_id} not found")
            return pd.DataFrame()

        # Get user's high-rated destinations (score >= 4.0)
        user_ratings = self.user_item_matrix.loc[user_id]
        high_rated_dests = user_ratings[user_ratings >= 4.0]

        if len(high_rated_dests) == 0:
            print(f"User {user_id} has no high-rated destinations (>= 4.0)")
            return pd.DataFrame()

        print(f"User {user_id} has {len(high_rated_dests)} high-rated destinations")

        # Get recommendations from each high-rated destination
        all_recommendations = []
        seen_destinations = set(high_rated_dests.index)  # Don't recommend already rated destinations

        for dest_id, rating in high_rated_dests.items():
            similar_dests = self.get_similar_destinations(dest_id, rating, top_n=top_n*2)
            for _, row in similar_dests.iterrows():
                rec_dest_id = row['destination_id']
                if rec_dest_id not in seen_destinations:
                    # Check if user hasn't rated this destination yet
                    if rec_dest_id not in self.user_item_matrix.columns or self.user_item_matrix.loc[user_id, rec_dest_id] == 0:
                        all_recommendations.append({
                            'destination_id': rec_dest_id,
                            'name': row['name'],
                            'category': row['category'],
                            'rating': row['rating'],
                            'similarity_score': row['similarity_score']
                        })

        # Remove duplicates and sort by similarity score
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec['destination_id'] not in seen:
                unique_recommendations.append(rec)
                seen.add(rec['destination_id'])

        # Sort by similarity score
        unique_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)

        return pd.DataFrame(unique_recommendations[:top_n])

    def get_popular_destinations(self, top_n: int = 10) -> pd.DataFrame:
        """Get most popular destinations based on average ratings"""
        if self.user_item_matrix is None:
            return pd.DataFrame()

        # Calculate average rating for each destination
        dest_ratings = {}
        for dest_id in self.user_item_matrix.columns:
            ratings = self.user_item_matrix[dest_id][self.user_item_matrix[dest_id] > 0]
            if len(ratings) > 0:
                dest_ratings[dest_id] = ratings.mean()

        # Sort by average rating
        sorted_dests = sorted(dest_ratings.items(), key=lambda x: x[1], reverse=True)

        # Convert to DataFrame with destination info
        results = []
        for dest_id, avg_rating in sorted_dests[:top_n]:
            dest_info = self.destinations_df.loc[dest_id] if dest_id in self.destinations_df.index else None
            if dest_info is not None:
                results.append({
                    'destination_id': dest_id,
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'average_user_rating': avg_rating
                })

        return pd.DataFrame(results)


# Singleton instance
_recommender_instance = None

def get_recommender() -> CollaborativeRecommender:
    """Get singleton instance of the recommender"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = CollaborativeRecommender()
    return _recommender_instance


# Example usage
if __name__ == "__main__":
    recommender = get_recommender()

    # Test recommendations for a user
    test_user = "user_001"
    recommendations = recommender.recommend_for_user(test_user, top_n=5)

    print(f"\nRecommendations for {test_user}:")
    if not recommendations.empty:
        for _, row in recommendations.iterrows():
            print(f"- {row['name']} ({row['category']}) - Score: {row['similarity_score']:.3f}")
    else:
        print("No recommendations available")

    # Test similar destinations
    test_destination = "dest_001"
    similar = recommender.get_similar_destinations(test_destination, 5.0, top_n=5)

    print(f"\nDestinations similar to {test_destination}:")
    if not similar.empty:
        for _, row in similar.iterrows():
            print(f"- {row['name']} ({row['category']}) - Similarity: {row['similarity_score']:.3f}")
    else:
        print("No similar destinations found")