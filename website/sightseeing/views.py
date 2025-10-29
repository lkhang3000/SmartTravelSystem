from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import *
import json
import os

# local recommender
from .Services.recommender import SightseeingRecommender


# Create your views here.
def get_home(request):
    #destination = Destinations.desName.all()
    return render(request, 'homepage.html')


def user_input(request):
    return render(request, 'userInput.html')


def user_login(request):
    return render(request, 'login.html')


def login_page(request):
    return render(request, 'login_page.html')


def signup_page(request):
    return render(request, 'signup.html')


def password_reset(request):
    return render(request, 'password_reset.html')


def password_reset_done(request):
    return render(request, 'password_reset_done.html')


def password_reset_confirm(request):
    return render(request, 'password_reset_confirm.html')


def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')


def api_recommend(request):
    """POST endpoint for frontend to submit user preferences.

    Behavior:
    - Accepts JSON body describing a single user (or a dict with key `user`).
    - Writes that user into `Services/user_data.json` as {"users": [user]}.
    - Calls the recommender to compute a recommendation for that user.
    - Writes the recommendation into `Services/recommendations/recommend_<username>.json`.
    - Returns the recommendation JSON to the client.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    # allow either raw user dict or {"user": {...}}
    user_data = payload.get('user') if isinstance(payload, dict) and 'user' in payload else payload

    if not isinstance(user_data, dict):
        return JsonResponse({"error": "Expected a user JSON object"}, status=400)

    # ensure Services path exists
    services_dir = os.path.join(os.path.dirname(__file__), 'Services')
    os.makedirs(services_dir, exist_ok=True)
    users_path = os.path.join(services_dir, 'user_data.json')

    # Save as a users list so the recommender utilities can read it later if needed
    try:
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump({"users": [user_data]}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        return JsonResponse({"error": "Failed to write user file", "details": str(e)}, status=500)

    # Instantiate recommender and compute recommendation for this user
    spots_path = os.path.join(services_dir, 'sightseeing_spots.json')
    recommender = SightseeingRecommender(spots_path, users_path)
    try:
        result = recommender.recommend_for_user(user_data)
    except Exception as e:
        return JsonResponse({"error": "Recommendation error", "details": str(e)}, status=500)

    # Write recommendation result into recommendations folder
    rec_dir = os.path.join(services_dir, 'recommendations')
    os.makedirs(rec_dir, exist_ok=True)
    username = (user_data.get('user_info', {}) or {}).get('username') or user_data.get('username') or 'unknown'
    safe_name = str(username).replace(' ', '_')
    out_path = os.path.join(rec_dir, f"recommend_{safe_name}.json")
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
    except Exception:
        # don't fail the whole request if writing the file fails; return the result anyway
        pass

    return JsonResponse(result)







