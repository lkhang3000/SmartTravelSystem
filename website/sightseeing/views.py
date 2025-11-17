from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
import json
import os
from datetime import datetime
from .Services.recommender import SightseeingRecommender, SightseeingSpot

@ensure_csrf_cookie
def get_home(request):
    #destination = Destinations.desName.all()
    return render(request, 'homepage.html')

def login_page(request):
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else: messages.info(request, 'user or password is incorrect!')
    return render(request, 'loginPage.html')

def signup_page(request):
    if request.method == "POST":
        form = registerForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login_page')
    else:
        form = registerForm()
    
    context = {'form': form}
    return render(request, 'signupPage.html', context)

def password_reset(request):
    return render(request, 'password_reset.html')

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

def password_reset_confirm(request):
    return render(request, 'password_reset_confirm.html')

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')

def recommend_result(request):
    """Display personalized recommendations based on user preferences"""
    # Get user data from session or use default
    user_data = request.session.get('user_preferences', None)
    
    recommendations = []
    
    if user_data:
        # Initialize recommender
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spots_file = os.path.join(base_dir, 'sightseeing', 'Services', 'sightseeing_spots.json')
        users_file = os.path.join(base_dir, 'sightseeing', 'Services', 'user_data.json')
        
        try:
            recommender = SightseeingRecommender(spots_file, users_file)
            
            # Get filtered recommendations based on user preferences
            preferences = user_data.get('trip_preferences', {})
            region = preferences.get('domestic_or_international', {}).get('region', '').lower()
            tags = [t.lower() for t in preferences.get('tags', [])]
            
            filtered = recommender.spots
            
            # Filter by region
            if region:
                filtered = [spot for spot in filtered if region in spot.region.lower()] or filtered
            
            # Filter by tags
            if tags:
                filtered = [
                    spot for spot in filtered
                    if any(tag in spot.category.lower() or tag in spot.name.lower() for tag in tags)
                ] or filtered
            
            # Sort by rating
            filtered.sort(key=lambda s: s.rating, reverse=True)
            
            # Get top 6 recommendations
            recommendations = [spot.to_dict() for spot in filtered[:6]]
            
        except Exception as e:
            messages.error(request, f'Error loading recommendations: {str(e)}')
    
    # If no recommendations, use default spots
    if not recommendations:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spots_file = os.path.join(base_dir, 'sightseeing', 'Services', 'sightseeing_spots.json')
        
        try:
            with open(spots_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                spots_data = data.get('locations', [])
                # Sort by rating and get top 6
                spots_data.sort(key=lambda x: x.get('rating', 0), reverse=True)
                recommendations = spots_data[:6]
        except:
            # Fallback to empty list
            pass
    
    context = {
        'recommendations': recommendations,
        'user_preferences': user_data
    }
    
    return render(request, 'recommendResult.html', context)

def user_profile(request):
    return render(request, 'userProfile.html')

def user_input(request):
    return render(request, 'userInput.html')

def destination(request):
    return render(request, 'destination,html')

def save_user_input(request):
    """Xử lý form và tạo file JSON cho recommender"""
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        username = request.POST.get('username', 'anonymous')
        region = request.POST.get('region')
        budget = request.POST.get('budget')
        departure_date = request.POST.get('departure_date')
        return_date = request.POST.get('return_date')
        num_people = request.POST.get('num_people', 1)
        tags = request.POST.getlist('tags', [])  # Get multiple tags if provided
        
        # Tạo cấu trúc JSON theo format của recommender
        user_data = {
            "user_info": {
                "username": username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "trip_preferences": {
                "domestic_or_international": {
                    "type": "domestic",
                    "region": region
                },
                "tags": tags,
                "budget": int(budget) if budget else 0,
                "departure_date": departure_date if departure_date else None,
                "return_date": return_date if return_date else None,
                "num_people": int(num_people) if num_people else 1
            }
        }
        
        # Save to session for use in recommend_result
        request.session['user_preferences'] = user_data
        
        # Tạo thư mục nếu chưa tồn tại
        input_folder = os.path.join('sightseeing', 'Services', 'user_inputs')
        os.makedirs(input_folder, exist_ok=True)
        
        # Lưu file JSON
        filename = f"user_input_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(input_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)
        
        messages.success(request, f'✅ Đã lưu thông tin! Generating recommendations...')
        
        # Redirect to recommendation results
        return redirect('recommend_result')
    
    return redirect('user_input')
def about_us(request):
    return render(request, 'About-us.html')

def contact_us(request):
    return render(request, 'Contact-us.html')









