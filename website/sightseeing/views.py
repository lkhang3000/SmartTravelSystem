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
    return render(request, 'recommendResult.html')

def user_profile(request):
    return render(request, 'userProfile.html')

def user_input(request):
    return render(request, 'userInput.html')


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
                "tags": [],  # Có thể thêm sau
                "budget": int(budget) if budget else 0,
                "departure_date": departure_date if departure_date else None,
                "return_date": return_date if return_date else None,
                "num_people": int(num_people) if num_people else 1
            }
        }
        
        # Tạo thư mục nếu chưa tồn tại
        input_folder = os.path.join('sightseeing', 'Services', 'user_inputs')
        os.makedirs(input_folder, exist_ok=True)
        
        # Lưu file JSON
        filename = f"user_input_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(input_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)
        
        messages.success(request, f'✅ Đã lưu thông tin! File: {filename}')
        
        # Redirect về trang user_input hoặc trang kết quả
        return redirect('user_input')
    
    return redirect('user_input')
def about_us(request):
    return render(request, 'About-us.html')

def contact_us(request):
    return render(request, 'Contact-us.html')









