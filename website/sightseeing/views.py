from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import *
from datetime import datetime
import json
import os

# local recommender
from .Services.recommender import SightseeingRecommender

# Create your views here.
def get_home(request):
    destination = Destinations.desName.all()
    return render (request, 'homepage.html')

def user_input(request):
    return render(request, 'userInput.html')

def user_login(request):
    return render(request, 'login.html')

def api_recommend(request):
    """Accept POST JSON from frontend, save to Services/user_data.json,
    run the recommender for that user and return the recommendation JSON.

    Expected POST body: a single user object matching the structure in
    `Services/user_data.json` (i.e. keys like `user_info`, `trip_preferences`, ...).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    # Normalize payload to a single user dict
    user_data = payload
    # Ensure timestamp exists
    user_data.setdefault('timestamp', datetime.utcnow().isoformat() + "Z")

    # Paths to service files
    services_dir = os.path.join(os.path.dirname(__file__), 'Services')
    spots_file = os.path.join(services_dir, 'sightseeing_spots.json')
    users_file = os.path.join(services_dir, 'user_data.json')
    recommendations_dir = os.path.join(services_dir, 'recommendations')

    # Save incoming user to `user_data.json` (overwrites with single-user list)
    os.makedirs(services_dir, exist_ok=True)
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump({"users": [user_data]}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        return JsonResponse({"error": f"Failed to write user file: {e}"}, status=500)

    # Run recommender (instantiate and call recommend_for_user)
    try:
        recommender = SightseeingRecommender(spots_file, users_file)
        result = recommender.recommend_for_user(user_data)
    except Exception as e:
        return JsonResponse({"error": f"Recommender error: {e}"}, status=500)

    # Persist recommendation result to recommendations folder
    try:
        os.makedirs(recommendations_dir, exist_ok=True)
        username = result.get('username', f'user_{int(datetime.utcnow().timestamp())}')
        output_path = os.path.join(recommendations_dir, f"recommend_{username}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
    except Exception:
        # Non-fatal: continue and return result even if save fails
        pass

    return JsonResponse(result, status=200)