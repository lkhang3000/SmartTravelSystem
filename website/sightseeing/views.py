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
    # Get all locations and categories for filter dropdowns
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None values
    
    context = {
        'all_locations': all_locations,
        'all_categories': all_categories,
    }
    return render(request, 'homepage.html', context)

def login_page(request):
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('user_profile')  # Chuyển về profile thay vì home
        else: 
            messages.error(request, 'Username or password is incorrect!')
    return render(request, 'loginPage.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def signup_page(request):
    from django.contrib.auth import login
    
    if request.method == "POST":
        form = registerForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tự động đăng nhập sau khi đăng ký
            login(request, user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Welcome {username}! Your account has been created successfully.')
            return redirect('user_profile')  # Chuyển về trang profile
        else:
            # Thêm thông báo lỗi
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = registerForm()
    
    context = {'form': form}
    return render(request, 'signupPage.html', context)

def password_reset(request):
    from django.contrib.auth.models import User
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = request.build_absolute_uri(
                f'/password-reset/confirm/?uid={uid}&token={token}'
            )
            
            # Send email (you need to configure email settings in settings.py)
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click the link below to reset your password:\n\n{reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset link has been sent to your email!')
                return redirect('password_reset_done')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'password_reset.html')

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

def password_reset_confirm(request):
    from django.contrib.auth.models import User
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    
    uid = request.GET.get('uid')
    token = request.GET.get('token')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'password_reset_confirm.html')
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully!')
                return redirect('password_reset_complete')
            else:
                messages.error(request, 'Invalid or expired reset link.')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'Invalid reset link.')
    
    return render(request, 'password_reset_confirm.html')

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')

def recommend_result(request):
    """Display personalized recommendations based on user preferences and filters"""
    from django.db.models import Q
    
    # Get user data from session or use default
    user_data = request.session.get('user_preferences', None)
    
    # Start with all destinations from database
    destinations_query = Destinations.objects.all().select_related('location')
    
    # Get filter parameters from GET request
    selected_location = request.GET.get('location', '')
    selected_category = request.GET.get('category', '')
    selected_price = request.GET.get('price', '')
    selected_rating = request.GET.get('rating', '')
    
    # Apply filters from URL parameters (priority over session data)
    if selected_location:
        destinations_query = destinations_query.filter(location__id=selected_location)
    elif user_data:
        # Fall back to session data if no URL filter
        preferences = user_data.get('trip_preferences', {})
        location_name = preferences.get('domestic_or_international', {}).get('region', '')
        if location_name:
            destinations_query = destinations_query.filter(
                location__locationName__icontains=location_name
            )
    
    # Filter by category
    if selected_category:
        destinations_query = destinations_query.filter(category__icontains=selected_category)
    elif user_data:
        # Fall back to session tags
        preferences = user_data.get('trip_preferences', {})
        tags = [t.lower() for t in preferences.get('tags', [])]
        if tags:
            tag_filter = Q()
            for tag in tags:
                tag_filter |= Q(category__icontains=tag) | Q(desName__icontains=tag)
            destinations_query = destinations_query.filter(tag_filter)
    
    # Filter by price range
    if selected_price:
        if selected_price == 'free':
            destinations_query = destinations_query.filter(
                Q(price_range__icontains='free') | Q(price_range__icontains='miễn phí')
            )
        elif selected_price == 'budget':
            destinations_query = destinations_query.filter(
                Q(price_range__icontains='50k') | Q(price_range__icontains='100k') | 
                Q(price_range__icontains='150k') | Q(price_range__icontains='budget')
            )
        elif selected_price == 'medium':
            destinations_query = destinations_query.filter(
                Q(price_range__icontains='200k') | Q(price_range__icontains='300k') | 
                Q(price_range__icontains='400k') | Q(price_range__icontains='500k')
            )
        elif selected_price == 'premium':
            destinations_query = destinations_query.filter(
                Q(price_range__icontains='600k') | Q(price_range__icontains='1000k') | 
                Q(price_range__icontains='million') | Q(price_range__icontains='premium')
            )
    
    # Filter by rating
    if selected_rating:
        try:
            min_rating = float(selected_rating)
            destinations_query = destinations_query.filter(rating__gte=min_rating)
        except ValueError:
            pass
    
    # Sort by rating (highest first)
    recommendations = destinations_query.order_by('-rating')
    
    # Convert to list of dicts for template
    recommendations_list = []
    for dest in recommendations:
        recommendations_list.append({
            'id': dest.id,
            'name': dest.desName,
            'location': dest.location.locationName if dest.location else 'Unknown',
            'category': dest.category or 'General',
            'rating': dest.rating or 0.0,
            'address': dest.address or '',
            'description': dest.description or '',
            'price_range': dest.price_range or 'Contact for pricing',
            'image_url': dest.image_url or 'https://picsum.photos/seed/default/800/600',
        })
    
    # Get all locations and categories for filter dropdowns
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None values
    
    context = {
        'recommendations': recommendations_list,
        'user_preferences': user_data,
        'all_locations': all_locations,
        'all_categories': all_categories,
        'selected_location': selected_location,
        'selected_category': selected_category,
        'selected_price': selected_price,
        'selected_rating': selected_rating,
        'total_results': len(recommendations_list),
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

def trip_planner(request):
    return render(request, 'Trip-planner.html')









