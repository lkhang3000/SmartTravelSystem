"""
recommender.py
---------------
Hybrid Recommender System for Travel Destinations
Combines Collaborative Filtering + Content-Based Recommendations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import os
import django
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import NMF
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import pickle
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from sightseeing.models import SearchHistory, Destinations, UsersProfile, UserRating

def cosine_similarity_matrix(matrix: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity matrix without scikit-learn"""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized_matrix = matrix / norms
    similarity = np.dot(normalized_matrix, normalized_matrix.T)
    return similarity

class ContentSimilarityRecommender:
    """Content similarity recommender using destination features (formerly ContentBasedRecommender)"""

    def __init__(self):
        self.destinations_df = None
        self.tfidf_matrix = None
        self.feature_matrix = None
        self._load_data()
        self._build_content_features()

    def _load_data(self):
        """Load destinations data"""
        destinations = Destinations.objects.all().values(
            'destination_id', 'desName', 'category', 'rating',
            'location', 'description'
        )
        self.destinations_df = pd.DataFrame(list(destinations))
        self.destinations_df.set_index('destination_id', inplace=True)

    def _build_content_features(self):
        """Build content features for destinations"""
        if self.destinations_df.empty:
            return

        # Text features from name, category, location, description
        text_features = []
        for idx, row in self.destinations_df.iterrows():
            text = f"{row['desName']} {row['category']} {row.get('location', '')} {row.get('description', '')}"
            text_features.append(text)

        # TF-IDF for text similarity
        if text_features:
            tfidf = TfidfVectorizer(stop_words='english', max_features=100)
            self.tfidf_matrix = tfidf.fit_transform(text_features)

        # Numeric features
        numeric_features = []
        for idx, row in self.destinations_df.iterrows():
            features = [
                row.get('rating', 0)
            ]
            numeric_features.append(features)

        # Scale numeric features
        if numeric_features:
            scaler = StandardScaler()
            scaled_numeric = scaler.fit_transform(numeric_features)

            # Combine TF-IDF and numeric features
            if self.tfidf_matrix is not None:
                self.feature_matrix = np.hstack([self.tfidf_matrix.toarray(), scaled_numeric])
            else:
                self.feature_matrix = scaled_numeric

    def get_similar_by_content(self, destination_id: str, top_n: int = 10) -> pd.DataFrame:
        """Get destinations similar by content features"""
        if self.feature_matrix is None or destination_id not in self.destinations_df.index:
            return pd.DataFrame()

        # Find index of destination
        dest_idx = self.destinations_df.index.get_loc(destination_id)

        # Calculate similarities
        similarities = cosine_similarity([self.feature_matrix[dest_idx]], self.feature_matrix)[0]

        # Get top similar (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:top_n+1]

        results = []
        for idx in similar_indices:
            dest_id = self.destinations_df.index[idx]
            dest_info = self.destinations_df.loc[dest_id]
            results.append({
                'destination_id': dest_id,
                'name': dest_info['desName'],
                'category': dest_info['category'],
                'rating': dest_info['rating'],
                'content_similarity': similarities[idx]
            })

        return pd.DataFrame(results)

    def recommend_by_preferences(self, user_preferences: Dict, top_n: int = 10) -> pd.DataFrame:
        """Recommend based on user preferences (category, budget, duration, etc.) with flexible category matching"""
        if self.destinations_df.empty:
            return pd.DataFrame()

        # Define related categories for flexible matching
        category_relations = {
            'Entertainment': ['Entertainment', 'Temple', 'Beach', 'Museum', 'Park', 'Historical'],
            'Temple': ['Temple', 'Historical', 'Cultural', 'Religious', 'Museum'],
            'Beach': ['Beach', 'Resort', 'Adventure', 'Nature', 'Relaxation'],
            'Museum': ['Museum', 'Historical', 'Cultural', 'Educational', 'Art'],
            'Park': ['Park', 'Nature', 'Recreation', 'Outdoor', 'Relaxation'],
            'Historical': ['Historical', 'Museum', 'Cultural', 'Temple', 'Monument'],
            'Cultural': ['Cultural', 'Museum', 'Historical', 'Temple', 'Traditional'],
            'Nature': ['Nature', 'Park', 'Beach', 'Mountain', 'Adventure'],
            'Adventure': ['Adventure', 'Nature', 'Beach', 'Mountain', 'Sports'],
            'Relaxation': ['Relaxation', 'Beach', 'Park', 'Spa', 'Resort']
        }

        # Keywords that indicate entertainment value
        entertainment_keywords = [
            'festival', 'celebration', 'event', 'show', 'performance', 'music', 'dance',
            'party', 'fun', 'entertainment', 'amusement', 'recreation', 'activity',
            'experience', 'attraction', 'tourist', 'visitor', 'popular', 'famous'
        ]

        scored_destinations = []

        for dest_id, dest_info in self.destinations_df.iterrows():
            score = 0.0
            category = dest_info['category']
            name = dest_info['desName'].lower()
            description = str(dest_info.get('description', '')).lower()

            # Category preference with flexible matching
            if 'category' in user_preferences:
                user_category = user_preferences['category']

                # Exact category match - highest score
                if category == user_category:
                    score += 0.4

                # Related category match - medium score
                elif user_category in category_relations and category in category_relations[user_category]:
                    score += 0.25

                # Special case: Entertainment can match destinations with entertainment keywords
                elif user_category == 'Entertainment':
                    has_entertainment_keywords = any(keyword in name or keyword in description
                                                   for keyword in entertainment_keywords)
                    if has_entertainment_keywords:
                        score += 0.2

            # Rating preference - higher rating gets bonus
            rating = dest_info.get('rating', 0)
            if rating >= 4.5:
                score += 0.15
            elif rating >= 4.0:
                score += 0.1
            elif rating >= 3.5:
                score += 0.05

            # Location preference (if provided)
            if 'location' in user_preferences and dest_info.get('location') == user_preferences['location']:
                score += 0.1

            # Only include destinations with some relevance
            if score > 0:
                scored_destinations.append({
                    'destination_id': dest_id,
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'preference_score': score
                })

        # Sort by preference score
        scored_destinations.sort(key=lambda x: x['preference_score'], reverse=True)
        return pd.DataFrame(scored_destinations[:top_n])

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

class AIRecommender:
    """AI-Powered Recommender using Matrix Factorization (NMF) + Neural Network (MLP)"""

    def __init__(self):
        self.nmf_model = None  # Matrix Factorization model
        self.mlp_model = None  # Neural network model
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.num_users = 0
        self.num_items = 0
        self.user_item_matrix = None
        self.model_path = os.path.join(settings.BASE_DIR, 'sightseeing', 'Services', 'ai_models')
        os.makedirs(self.model_path, exist_ok=True)
        self._load_data()
        self._load_or_train_models()

    def _load_data(self):
        """Load and prepare data for AI models using combined SearchHistory and UserRating"""
        try:
            # Load search history
            search_entries = SearchHistory.objects.all().values('user_id', 'destination_id', 'score')
            search_df = pd.DataFrame(list(search_entries)) if search_entries else pd.DataFrame()
            
            # Load user ratings
            rating_entries = UserRating.objects.select_related('user__usersprofile').values(
                'user__usersprofile__custom_user_id', 'destination__destination_id', 'rating'
            )
            rating_df = pd.DataFrame(list(rating_entries)) if rating_entries else pd.DataFrame()
            
            # Rename columns for consistency
            if not rating_df.empty:
                rating_df = rating_df.rename(columns={
                    'user__usersprofile__custom_user_id': 'user_id',
                    'destination__destination_id': 'destination_id'
                })
            
            # Combine data
            combined_df = pd.concat([search_df, rating_df], ignore_index=True)
            
            if not combined_df.empty:
                # Convert destination_id format
                combined_df['destination_id'] = combined_df['destination_id'].astype(str)
                combined_df['destination_id'] = combined_df['destination_id'].apply(
                    lambda x: f"dest_{int(x):03d}" if x.isdigit() else x
                )
                
                # Group by user and destination, calculate average rating
                combined_df = combined_df.groupby(['user_id', 'destination_id']).agg({
                    'score': 'mean',
                    'rating': 'mean'
                }).reset_index()
                
                # Create final score: average of available scores, scaled to 0-5.0
                combined_df['final_score'] = combined_df[['score', 'rating']].mean(axis=1, skipna=True)
                combined_df['final_score'] = combined_df['final_score'].fillna(combined_df['score']).fillna(combined_df['rating'])
                combined_df['final_score'] = combined_df['final_score'].clip(0, 5.0)
                
                # Create mappings
                unique_users = combined_df['user_id'].unique()
                unique_items = combined_df['destination_id'].unique()

                self.user_id_map = {user: idx for idx, user in enumerate(unique_users)}
                self.item_id_map = {item: idx for idx, item in enumerate(unique_items)}
                self.reverse_user_map = {v: k for k, v in self.user_id_map.items()}
                self.reverse_item_map = {v: k for k, v in self.item_id_map.items()}

                self.num_users = len(unique_users)
                self.num_items = len(unique_items)

                # Create user-item matrix
                self.user_item_matrix = np.zeros((self.num_users, self.num_items))
                for _, row in combined_df.iterrows():
                    user_idx = self.user_id_map[row['user_id']]
                    item_idx = self.item_id_map[row['destination_id']]
                    self.user_item_matrix[user_idx, item_idx] = row['final_score']

                print(f"✓ AI Recommender loaded: {self.num_users} users, {self.num_items} items, {len(combined_df)} ratings")
                print(f"  Average rating: {combined_df['final_score'].mean():.2f}")
            else:
                print("No training data for AI Recommender")
                self.user_item_matrix = None

        except Exception as e:
            print(f"Error loading AI data: {e}")
            self.user_item_matrix = None

    def _load_or_train_models(self):
        """Load existing models or train new ones"""
        nmf_path = os.path.join(self.model_path, 'nmf_model.pkl')
        mlp_path = os.path.join(self.model_path, 'mlp_model.pkl')

        # Try to load existing models
        if os.path.exists(nmf_path) and os.path.exists(mlp_path):
            try:
                with open(nmf_path, 'rb') as f:
                    self.nmf_model = pickle.load(f)
                with open(mlp_path, 'rb') as f:
                    self.mlp_model = pickle.load(f)
                print("✓ Loaded existing AI models (NMF + MLP)")
                return
            except Exception as e:
                print(f"Error loading models: {e}")

        # Train new models
        if self.user_item_matrix is not None and self.user_item_matrix.size > 0:
            self._train_models()
            # Save models
            try:
                with open(nmf_path, 'wb') as f:
                    pickle.dump(self.nmf_model, f)
                with open(mlp_path, 'wb') as f:
                    pickle.dump(self.mlp_model, f)
                print("✓ Saved trained AI models")
            except Exception as e:
                print(f"Error saving models: {e}")

    def _train_models(self):
        """Train both NMF (Matrix Factorization) and MLP (Neural Network) models"""
        if self.user_item_matrix is None or self.user_item_matrix.size == 0:
            return

        print("🤖 Training AI models (NMF + MLP Neural Network)...")

        # 1. Train NMF for Matrix Factorization
        n_components = min(20, min(self.num_users, self.num_items) - 1)
        self.nmf_model = NMF(n_components=n_components, init='random', random_state=42, max_iter=200)
        
        # Replace zeros with small values to avoid issues
        matrix_for_nmf = self.user_item_matrix.copy()
        matrix_for_nmf[matrix_for_nmf == 0] = 0.1
        
        W = self.nmf_model.fit_transform(matrix_for_nmf)  # User features
        H = self.nmf_model.components_  # Item features

        # 2. Train MLP (Neural Network) for rating prediction
        # Prepare training data from existing ratings
        train_data = []
        train_labels = []
        
        for user_idx in range(self.num_users):
            for item_idx in range(self.num_items):
                if self.user_item_matrix[user_idx, item_idx] > 0:
                    # Combine user and item features from NMF
                    features = np.concatenate([W[user_idx], H[:, item_idx]])
                    train_data.append(features)
                    train_labels.append(self.user_item_matrix[user_idx, item_idx])

        if len(train_data) > 0:
            X_train = np.array(train_data)
            y_train = np.array(train_labels)

            # Train MLP Neural Network
            self.mlp_model = MLPRegressor(
                hidden_layer_sizes=(64, 32, 16),
                activation='relu',
                solver='adam',
                max_iter=200,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )
            self.mlp_model.fit(X_train, y_train)
            
            score = self.mlp_model.score(X_train, y_train)
            print(f"✓ AI models trained successfully! Accuracy: {score:.1%}")

    def predict_rating(self, user_id: str, item_id: str) -> float:
        """AI-powered rating prediction using NMF + MLP"""
        if not self.nmf_model or not self.mlp_model:
            return 0.0
            
        if user_id not in self.user_id_map or item_id not in self.item_id_map:
            return 0.0

        try:
            user_idx = self.user_id_map[user_id]
            item_idx = self.item_id_map[item_id]

            # Get features from NMF
            matrix_for_pred = self.user_item_matrix.copy()
            matrix_for_pred[matrix_for_pred == 0] = 0.1
            W = self.nmf_model.transform(matrix_for_pred)
            H = self.nmf_model.components_

            # Combine features
            features = np.concatenate([W[user_idx], H[:, item_idx]])
            features = features.reshape(1, -1)

            # Predict using MLP
            prediction = self.mlp_model.predict(features)[0]
            return float(max(0.0, min(5.0, prediction)))  # Clamp between 0-5

        except Exception as e:
            return 0.0

    def recommend_for_user(self, user_id: str, top_n: int = 10) -> pd.DataFrame:
        """AI-powered recommendations for user"""
        if not self.nmf_model or not self.mlp_model or user_id not in self.user_id_map:
            return pd.DataFrame()

        # Get all items user hasn't rated highly
        user_idx = self.user_id_map[user_id]
        user_ratings = self.user_item_matrix[user_idx]

        predictions = []
        for item_id, item_idx in self.item_id_map.items():
            # Skip items user has already rated highly
            if user_ratings[item_idx] < 4.0:
                predicted_rating = self.predict_rating(user_id, item_id)
                if predicted_rating > 3.0:  # Only recommend items with good predictions
                    predictions.append({
                        'destination_id': item_id,
                        'predicted_rating': predicted_rating
                    })

        # Sort by predicted rating
        predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)

        # Get destination info
        results = []
        for pred in predictions[:top_n]:
            dest_info = self._get_destination_info(pred['destination_id'])
            if dest_info:
                results.append({
                    'destination_id': pred['destination_id'],
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'predicted_rating': pred['predicted_rating']
                })

        return pd.DataFrame(results)

    def _get_destination_info(self, dest_id: str) -> Dict:
        """Get destination information"""
        try:
            dest = Destinations.objects.get(destination_id=dest_id)
            return {
                'desName': dest.desName,
                'category': dest.category,
                'rating': dest.rating
            }
        except Destinations.DoesNotExist:
            return None


class NeuralRecommender:
    """Neural Collaborative Filtering using GMF + MLP architecture"""

    def __init__(self):
        self.model = None
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.num_users = 0
        self.num_items = 0
        self.embedding_dim = 50
        self._load_data()
        self._build_model()
        self._load_or_train_model()

    def _load_data(self):
        """Load and prepare data for neural network using combined ratings"""
        try:
            # Load search history
            search_entries = SearchHistory.objects.all().values('user_id', 'destination_id', 'score')
            search_df = pd.DataFrame(list(search_entries)) if search_entries else pd.DataFrame()
            
            # Load user ratings
            rating_entries = UserRating.objects.select_related('user__usersprofile').values(
                'user__usersprofile__custom_user_id', 'destination__destination_id', 'rating'
            )
            rating_df = pd.DataFrame(list(rating_entries)) if rating_entries else pd.DataFrame()
            
            # Rename columns for consistency
            if not rating_df.empty:
                rating_df = rating_df.rename(columns={
                    'user__usersprofile__custom_user_id': 'user_id',
                    'destination__destination_id': 'destination_id'
                })
            
            # Combine data
            combined_df = pd.concat([search_df, rating_df], ignore_index=True)
            
            if not combined_df.empty:
                # Convert destination_id format
                combined_df['destination_id'] = combined_df['destination_id'].astype(str)
                combined_df['destination_id'] = combined_df['destination_id'].apply(
                    lambda x: f"dest_{int(x):03d}" if x.isdigit() else x
                )
                
                # Group by user and destination, calculate average rating
                combined_df = combined_df.groupby(['user_id', 'destination_id']).agg({
                    'score': 'mean',
                    'rating': 'mean'
                }).reset_index()
                
                # Create final score: average of available scores, scaled to 0-5.0
                combined_df['final_score'] = combined_df[['score', 'rating']].mean(axis=1, skipna=True)
                combined_df['final_score'] = combined_df['final_score'].fillna(combined_df['score']).fillna(combined_df['rating'])
                combined_df['final_score'] = combined_df['final_score'].clip(0, 5.0)
                
                # Create mappings
                unique_users = combined_df['user_id'].unique()
                unique_items = combined_df['destination_id'].unique()

                self.user_id_map = {user: idx for idx, user in enumerate(unique_users)}
                self.item_id_map = {item: idx for idx, item in enumerate(unique_items)}
                self.reverse_user_map = {v: k for k, v in self.user_id_map.items()}
                self.reverse_item_map = {v: k for k, v in self.item_id_map.items()}

                self.num_users = len(unique_users)
                self.num_items = len(unique_items)

                # Prepare training data
                user_indices = combined_df['user_id'].map(self.user_id_map)
                item_indices = combined_df['destination_id'].map(self.item_id_map)
                ratings = combined_df['final_score'].values

                self.train_data = {
                    'user_indices': user_indices.values,
                    'item_indices': item_indices.values,
                    'ratings': ratings
                }

                print(f"Neural CF: {self.num_users} users, {self.num_items} items, {len(ratings)} ratings")
                print(f"  Average rating: {ratings.mean():.2f}")
            else:
                print("No training data for Neural CF")
                self.train_data = None

        except Exception as e:
            print(f"Error loading neural data: {e}")
            self.train_data = None

    def _build_model(self):
        """Build GMF + MLP neural network"""
        if self.num_users == 0 or self.num_items == 0:
            return

        # Input layers
        user_input = layers.Input(shape=(1,), name='user_input')
        item_input = layers.Input(shape=(1,), name='item_input')

        # Embedding layers
        user_embedding = layers.Embedding(self.num_users, self.embedding_dim, name='user_embedding')(user_input)
        item_embedding = layers.Embedding(self.num_items, self.embedding_dim, name='item_embedding')(item_input)

        # Flatten embeddings
        user_flat = layers.Flatten()(user_embedding)
        item_flat = layers.Flatten()(item_embedding)

        # GMF (Generalized Matrix Factorization)
        gmf_product = layers.Multiply()([user_flat, item_flat])

        # MLP (Multi-Layer Perceptron)
        mlp_concat = layers.Concatenate()([user_flat, item_flat])
        mlp_layer1 = layers.Dense(64, activation='relu')(mlp_concat)
        mlp_layer2 = layers.Dense(32, activation='relu')(mlp_layer1)
        mlp_layer3 = layers.Dense(16, activation='relu')(mlp_layer2)

        # Concatenate GMF and MLP
        concat = layers.Concatenate()([gmf_product, mlp_layer3])

        # Output layer
        output = layers.Dense(1, activation='sigmoid')(concat)

        # Build model
        self.model = keras.Model(inputs=[user_input, item_input], outputs=output)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])

        print("Neural CF model built successfully")

    def _load_or_train_model(self):
        """Load existing model or train new one"""
        model_path = os.path.join(settings.BASE_DIR, 'sightseeing', 'Services', 'neural_model.h5')

        if os.path.exists(model_path):
            try:
                self.model = keras.models.load_model(model_path)
                print("Loaded existing neural model")
                return
            except Exception as e:
                print(f"Error loading model: {e}")

        # Train new model
        if self.train_data and self.model:
            self._train_model()
            # Save model
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.model.save(model_path)
            print("Saved trained neural model")

    def _train_model(self):
        """Train the neural network"""
        if not self.train_data:
            return

        # Prepare data
        user_indices = self.train_data['user_indices']
        item_indices = self.train_data['item_indices']
        ratings = self.train_data['ratings']

        # Normalize ratings to 0-1
        ratings_normalized = ratings / 5.0

        # Train model
        self.model.fit(
            [user_indices, item_indices],
            ratings_normalized,
            epochs=10,
            batch_size=32,
            validation_split=0.1,
            verbose=1
        )

    def predict_rating(self, user_id: str, item_id: str) -> float:
        """Predict rating for user-item pair"""
        if not self.model or user_id not in self.user_id_map or item_id not in self.item_id_map:
            return 0.0

        user_idx = self.user_id_map[user_id]
        item_idx = self.item_id_map[item_id]

        prediction = self.model.predict([[user_idx], [item_idx]], verbose=0)
        return float(prediction[0][0] * 5.0)  # Scale back to 0-5

    def recommend_for_user(self, user_id: str, top_n: int = 10) -> pd.DataFrame:
        """Recommend items for user using neural predictions"""
        if not self.model or user_id not in self.user_id_map:
            return pd.DataFrame()

        user_idx = self.user_id_map[user_id]
        predictions = []

        # Predict for all items
        for item_id, item_idx in self.item_id_map.items():
            predicted_rating = self.predict_rating(user_id, item_id)
            if predicted_rating > 0:
                predictions.append({
                    'destination_id': item_id,
                    'predicted_rating': predicted_rating
                })

        # Sort by predicted rating
        predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)

        # Get destination info
        results = []
        for pred in predictions[:top_n]:
            dest_info = self._get_destination_info(pred['destination_id'])
            if dest_info:
                results.append({
                    'destination_id': pred['destination_id'],
                    'name': dest_info['desName'],
                    'category': dest_info['category'],
                    'rating': dest_info['rating'],
                    'predicted_rating': pred['predicted_rating']
                })

        return pd.DataFrame(results)

    def _get_destination_info(self, dest_id: str) -> Dict:
        """Get destination information"""
        try:
            dest = Destinations.objects.get(destination_id=dest_id)
            return {
                'desName': dest.desName,
                'category': dest.category,
                'rating': dest.rating
            }
        except Destinations.DoesNotExist:
            return None

class HybridRecommender:
    """Hybrid recommender combining user behavior, content similarity, and AI methods"""

    def __init__(self):
        self.collaborative = UserBehaviorRecommender()
        self.content_based = ContentSimilarityRecommender()
        self.ai = AIRecommender()  # AI-powered recommender
        self.collab_weight = 0.4   # Weight for collaborative filtering
        self.content_weight = 0.3  # Weight for content-based
        self.ai_weight = 0.3       # Weight for AI predictions

    def recommend_for_user(self, user_id: str, user_preferences: Dict = None, top_n: int = 10) -> pd.DataFrame:
        """Hybrid recommendation for user using collaborative + content + AI"""
        recommendations = []

        # Get user behavior recommendations
        collab_recs = self.collaborative.recommend_for_user(user_id, top_n=top_n*3)
        collab_dict = {row['destination_id']: row for _, row in collab_recs.iterrows()}

        # Get content-based recommendations if preferences available
        content_recs = pd.DataFrame()
        if user_preferences:
            content_recs = self.content_based.recommend_by_preferences(user_preferences, top_n=top_n*3)
        content_dict = {row['destination_id']: row for _, row in content_recs.iterrows()}

        # Get AI recommendations
        ai_recs = self.ai.recommend_for_user(user_id, top_n=top_n*3)
        ai_dict = {row['destination_id']: row for _, row in ai_recs.iterrows()}

        # Combine all possible destinations
        all_dest_ids = set(collab_dict.keys()) | set(content_dict.keys()) | set(ai_dict.keys())

        for dest_id in all_dest_ids:
            collab_score = collab_dict.get(dest_id, {}).get('similarity_score', 0)
            content_score = content_dict.get(dest_id, {}).get('preference_score', 0)
            ai_score = ai_dict.get(dest_id, {}).get('predicted_rating', 0)

            # Normalize AI score to 0-1 range for weighting
            ai_score_norm = ai_score / 5.0 if ai_score > 0 else 0

            # Weighted combination with AI
            hybrid_score = (self.collab_weight * collab_score +
                          self.content_weight * content_score +
                          self.ai_weight * ai_score_norm)

            if hybrid_score > 0:
                # Get destination info
                dest_info = self.collaborative.destinations_df.loc[dest_id] if dest_id in self.collaborative.destinations_df.index else None
                if dest_info is not None:
                    recommendations.append({
                        'destination_id': dest_id,
                        'name': dest_info['desName'],
                        'category': dest_info['category'],
                        'rating': dest_info['rating'],
                        'hybrid_score': hybrid_score,
                        'collab_score': collab_score,
                        'content_score': content_score,
                        'ai_score': ai_score
                    })

        # Sort by hybrid score and return top_n
        recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return pd.DataFrame(recommendations[:top_n])

    def get_similar_destinations(self, destination_id: str, user_rating: float = 5.0,
                               user_preferences: Dict = None, top_n: int = 10) -> pd.DataFrame:
        """Hybrid similar destinations"""
        recommendations = []

        # User behavior similarity
        collab_similar = self.collaborative.get_similar_destinations(destination_id, user_rating, top_n=top_n*2)
        collab_dict = {row['destination_id']: row for _, row in collab_similar.iterrows()}

        # Content similarity
        content_similar = self.content_based.get_similar_by_content(destination_id, top_n=top_n*2)
        content_dict = {row['destination_id']: row for _, row in content_similar.iterrows()}

        # Combine
        all_dest_ids = set(collab_dict.keys()) | set(content_dict.keys())

        for dest_id in all_dest_ids:
            collab_score = collab_dict.get(dest_id, {}).get('similarity_score', 0)
            content_score = content_dict.get(dest_id, {}).get('content_similarity', 0)

            hybrid_score = (self.collab_weight * collab_score +
                          self.content_weight * content_score)

            if hybrid_score > 0:
                dest_info = self.collaborative.destinations_df.loc[dest_id] if dest_id in self.collaborative.destinations_df.index else None
                if dest_info is not None:
                    recommendations.append({
                        'destination_id': dest_id,
                        'name': dest_info['desName'],
                        'category': dest_info['category'],
                        'rating': dest_info['rating'],
                        'hybrid_score': hybrid_score
                    })

        recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return pd.DataFrame(recommendations[:top_n])

class UserBehaviorRecommender:
    """User behavior-based recommender using search history and ratings (formerly CollaborativeRecommender)"""

    def __init__(self):
        self.user_item_matrix = None
        self.item_similarity_df = None
        self.destinations_df = None
        self._load_data()
        self._build_similarity_matrix()

    def _load_data(self):
        """Load data from SearchHistory and UserRating models"""
        try:
            # Load search history data from database
            search_history_entries = SearchHistory.objects.all().values('user_id', 'destination_id', 'score')
            search_df = pd.DataFrame(list(search_history_entries)) if search_history_entries else pd.DataFrame()
            
            # Load user rating data from database
            user_rating_entries = UserRating.objects.select_related('user__usersprofile').values(
                'user__usersprofile__custom_user_id', 'destination__destination_id', 'rating'
            )
            rating_df = pd.DataFrame(list(user_rating_entries)) if user_rating_entries else pd.DataFrame()
            
            # Rename columns for consistency
            if not rating_df.empty:
                rating_df = rating_df.rename(columns={
                    'user__usersprofile__custom_user_id': 'user_id',
                    'destination__destination_id': 'destination_id'
                })
            
            print(f"Loaded {len(search_df)} search history records from database")
            print(f"Loaded {len(rating_df)} user rating records from database")
            
            # Combine search history and user ratings
            combined_df = pd.concat([search_df, rating_df], ignore_index=True)
            
            if not combined_df.empty:
                # Convert destination_id to proper format (dest_XXX)
                combined_df['destination_id'] = combined_df['destination_id'].astype(str)
                combined_df['destination_id'] = combined_df['destination_id'].apply(
                    lambda x: f"dest_{int(x):03d}" if x.isdigit() else x
                )
                
                # Group by user and destination, calculate average rating
                # This combines search scores and explicit ratings
                combined_df = combined_df.groupby(['user_id', 'destination_id']).agg({
                    'score': 'mean',  # For search history
                    'rating': 'mean'  # For user ratings
                }).reset_index()
                
                # Create final score: average of available scores, scaled to 0-5.0
                combined_df['final_score'] = combined_df[['score', 'rating']].mean(axis=1, skipna=True)
                
                # Fill NaN values (when only one type of rating exists)
                combined_df['final_score'] = combined_df['final_score'].fillna(combined_df['score']).fillna(combined_df['rating'])
                
                # Ensure score is within 0-5.0 range
                combined_df['final_score'] = combined_df['final_score'].clip(0, 5.0)
                
                print(f"Combined {len(combined_df)} unique user-destination ratings")
                
                # Create user-item matrix
                self.user_item_matrix = combined_df.pivot_table(
                    index='user_id',
                    columns='destination_id',
                    values='final_score',
                    fill_value=0
                )
                
                print(f"User-item matrix shape: {self.user_item_matrix.shape}")
                print(f"Total ratings: {(self.user_item_matrix > 0).sum().sum()}")
                print(f"Average rating: {self.user_item_matrix[self.user_item_matrix > 0].mean().mean():.2f}")
            else:
                print("No rating data available")
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

        # Get user's high-rated destinations (score >= 3.0)
        user_ratings = self.user_item_matrix.loc[user_id]
        high_rated_dests = user_ratings[user_ratings >= 3.0]

        if len(high_rated_dests) == 0:
            print(f"User {user_id} has no high-rated destinations (>= 3.0)")
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

def get_recommender() -> HybridRecommender:
    """Get singleton instance of the hybrid recommender"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = HybridRecommender()
    return _recommender_instance


# Example usage
if __name__ == "__main__":
    recommender = get_recommender()

    # Test hybrid recommendations for a user
    test_user = "user_001"
    user_prefs = {
        'category': 'Beach',
        'budget': 500
    }

    recommendations = recommender.recommend_for_user(test_user, user_preferences=user_prefs, top_n=5)

    print(f"\nHybrid Recommendations for {test_user}:")
    if not recommendations.empty:
        for _, row in recommendations.iterrows():
            print(f"- {row['name']} ({row['category']}) - Hybrid Score: {row['hybrid_score']:.3f}")
            print(f"  Collaborative: {row.get('collab_score', 0):.3f}, Content: {row.get('content_score', 0):.3f}")
    else:
        print("No recommendations available")

    # Test similar destinations
    test_destination = "dest_001"
    similar = recommender.get_similar_destinations(test_destination, user_rating=5.0,
                                                 user_preferences=user_prefs, top_n=5)

    print(f"\nHybrid similar destinations to {test_destination}:")
    if not similar.empty:
        for _, row in similar.iterrows():
            print(f"- {row['name']} ({row['category']}) - Hybrid Similarity: {row['hybrid_score']:.3f}")
    else:
        print("No similar destinations found")