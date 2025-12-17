from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
import json
import os
import traceback
from datetime import datetime, timedelta
from .Services.recommender import get_recommender
from django.core.paginator import Paginator
from sightseeing.models import Destinations, Hotel
import random
from django.http import JsonResponse
from datetime import datetime
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.db import transaction
from .models import Trip, TripItem, Destinations

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'reset_password_form.html'
    success_url = reverse_lazy('password_reset_complete')

@login_required
def change_email(request):
    if request.method == "POST":
        new_email = request.POST.get("new_email")
        current_password = request.POST.get("current_password")

        user = request.user

        if not user.check_password(current_password):
            messages.error(
                request,
                "Current password is incorrect.",
                extra_tags="change_email"
            )
            return redirect("user_profile")
        
        user.email = new_email
        user.save()

        messages.success(request, "Email updated successfully.")
        return redirect("user_profile")

@login_required
def change_password(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Kiểm tra password hiện tại
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('user_profile')  # hoặc trang profile của bạn

        # Kiểm tra password mới trùng
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return redirect('user_profile')

        # Update password
        user.set_password(new_password)
        user.save()

        # Giữ phiên đăng nhập sau khi đổi password
        update_session_auth_hash(request, user)

        messages.success(request, "Your password has been changed successfully.")
        return redirect('user_profile')

    return redirect('user_profile')

def update_trip(request):
    if request.method == "POST":
        start = request.POST.get("start_date")
        end = request.POST.get("end_date")
        travelers = request.POST.get("travelers")
        budget = request.POST.get("budget")

        # Lưu vào session — hoặc database nếu bạn muốn
        request.session["trip_start"] = start
        request.session["trip_end"] = end
        request.session["trip_travelers"] = travelers
        request.session["trip_budget"] = budget
        request.session.modified = True

        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "invalid"}, status=400)


@ensure_csrf_cookie
def get_home(request):
    # 1. Get filter data
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]

    # 2. Get specific IDs for carousel linking
    loc_danang = Location.objects.filter(locationName__icontains='Da Nang').first()
    loc_hcm = Location.objects.filter(locationName__icontains='Ho Chi Minh').first()
    loc_hanoi = Location.objects.filter(locationName__icontains='Hanoi').first()
    loc_hue = Location.objects.filter(locationName__icontains='Hue').first()
    loc_quangninh = Location.objects.filter(locationName__icontains='Quang Ninh').first()
    loc_phuquoc = Location.objects.filter(locationName__icontains='Phu Quoc').first()

    # 3. Personalized recommendations (Keeping your existing logic)
    personalized_recommendations = []
    # ... [Keep your existing recommendation code here] ...

    # 4. FETCH SAVED TRIPS (Crucial Step)
    saved_trips = []
    if request.user.is_authenticated:
        # Fetch top 3
        saved_trips = Trip.objects.filter(user=request.user).order_by('-updated_at')[:3]
        
        # Logic to find the best image for each card
        for trip in saved_trips:
            trip.display_image = f"https://picsum.photos/seed/{trip.destination}/800/400"
            if trip.destination:
                search_term = trip.destination.strip()
                dest = Destinations.objects.filter(desName__icontains=search_term).first()
                if dest:
                    # Uses the helper method you have in your Destinations model
                    images = dest.get_image_list() if hasattr(dest, 'get_image_list') else []
                    trip.display_image = images[0] if images else (dest.image_url or trip.display_image)
                else:
                    dest_in_loc = Destinations.objects.filter(location__locationName__icontains=search_term).first()
                    if dest_in_loc:
                        images = dest_in_loc.get_image_list() if hasattr(dest_in_loc, 'get_image_list') else []
                        trip.display_image = images[0] if images else (dest_in_loc.image_url or trip.display_image)

    # 5. CONTEXT (Add saved_trips here)
        try:
            recommender = get_recommender()
            user_profile = UsersProfile.objects.filter(user=request.user).first()
            if user_profile and user_profile.custom_user_id:
                # Get user preferences from session if available
                user_prefs = {}
                user_data = request.session.get('user_preferences')
                if user_data:
                    prefs = user_data.get('trip_preferences', {})
                    user_prefs = {
                        'category': ', '.join(prefs.get('tags', [])),
                        'budget': prefs.get('budget', 0)
                    }

                collab_recommendations = recommender.recommend_for_user(
                    user_profile.custom_user_id,
                    user_preferences=user_prefs,
                    top_n=6
                )
                if not collab_recommendations.empty:
                    print(f"Found {len(collab_recommendations)} personalized hybrid recommendations for homepage")
                    for _, row in collab_recommendations.iterrows():
                        try:
                            dest = Destinations.objects.get(destination_id=row['destination_id'])
                            rec_dict = {
                                'id': dest.id,
                                'name': dest.desName,
                                'location': dest.location.locationName if dest.location else 'Unknown',
                                'category': dest.category or 'General',
                                'rating': dest.rating or 0.0,
                                'image_url': dest.get_thumbnail_url() or 'https://picsum.photos/seed/default/400/300',
                                'hybrid_score': row['hybrid_score']
                            }
                            personalized_recommendations.append(rec_dict)
                        except Destinations.DoesNotExist:
                            continue
        except Exception as e:
            print(f"Error getting personalized hybrid recommendations: {e}")
    
    # Fallback to popular destinations if no personalized recommendations
    if not personalized_recommendations:
        try:
            recommender = get_recommender()
            popular_dests = recommender.get_popular_destinations(top_n=6)
            if not popular_dests.empty:
                for _, row in popular_dests.iterrows():
                    try:
                        dest = Destinations.objects.get(destination_id=row['destination_id'])
                        rec_dict = {
                            'id': dest.id,
                            'name': dest.desName,
                            'location': dest.location.locationName if dest.location else 'Unknown',
                            'category': dest.category or 'General',
                            'rating': dest.rating or 0.0,
                            'image_url': dest.get_thumbnail_url() or 'https://picsum.photos/seed/default/400/300',
                            'average_user_rating': row['average_user_rating']
                        }
                        personalized_recommendations.append(rec_dict)
                    except Destinations.DoesNotExist:
                        continue
        except Exception as e:
            print(f"Error getting popular destinations: {e}")
    
    context = {
        'all_locations': all_locations,
        'all_categories': all_categories,
        
        # Specific IDs for linking
        'danang_id': loc_danang.id if loc_danang else None,
        'hcm_id': loc_hcm.id if loc_hcm else None,
        'hanoi_id': loc_hanoi.id if loc_hanoi else None,
        'hue_id': loc_hue.id if loc_hue else None,
        'quangninh_id': loc_quangninh.id if loc_quangninh else None,
        'phuquoc_id': loc_phuquoc.id if loc_phuquoc else None,

        # New data for the homepage cards
        'saved_trips': saved_trips, 
        
        'selected_location': '',
        'selected_category': '',
        'selected_rating': '',
        'personalized_recommendations': personalized_recommendations,
        'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
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
    from django.db import transaction
    
    if request.method == "POST":
        form = registerForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Auto-create UsersProfile with custom_user_id using atomic transaction
            from .models import UsersProfile
            
            with transaction.atomic():
                # Generate unique user ID with retry logic
                max_attempts = 10
                for attempt in range(max_attempts):
                    try:
                        # Get the highest existing user number
                        existing_ids = UsersProfile.objects.filter(
                            custom_user_id__startswith='user_'
                        ).values_list('custom_user_id', flat=True)
                        
                        # Extract numbers from existing IDs
                        existing_nums = []
                        for existing_id in existing_ids:
                            try:
                                num = int(existing_id.split('_')[1])
                                existing_nums.append(num)
                            except (ValueError, IndexError):
                                continue
                        
                        # Find next available number
                        next_id = 1
                        if existing_nums:
                            next_id = max(existing_nums) + 1
                        
                        custom_user_id = f"user_{next_id:03d}"
                        
                        # Create profile with unique ID
                        user_profile = UsersProfile.objects.create(
                            user=user,
                            name=form.cleaned_data.get('first_name', '') + ' ' + form.cleaned_data.get('last_name', ''),
                            email=form.cleaned_data.get('email'),
                            custom_user_id=custom_user_id
                        )
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            # If all attempts failed, let it raise the exception
                            raise e
                        # Continue to next attempt
                
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
    from .Services.recommender import get_recommender

    # Get user data from session or use default
    user_data = request.session.get('user_preferences', None)

    # Get filter parameters from GET request
    selected_location = request.GET.get('location', '')
    if selected_location:
        try:
            selected_location = int(selected_location)
        except ValueError:
            selected_location = ''
    selected_category = request.GET.get('category', '')
    selected_price = request.GET.get('price', '')
    selected_rating = request.GET.get('rating', '')

    recommendations_list = []
    collaborative_recommendations = []
    search_results = []

    # Try collaborative filtering first if user is authenticated
    if request.user.is_authenticated:
        try:
            recommender = get_recommender()
            user_profile = UsersProfile.objects.filter(user=request.user).first()
            if user_profile and user_profile.custom_user_id:
                # Extract user preferences for hybrid recommender
                user_preferences = {}
                if user_data:
                    prefs = user_data.get('trip_preferences', {})
                    user_preferences = {
                        'category': selected_category or ', '.join(prefs.get('tags', [])),
                        'budget': prefs.get('budget', 0),
                        'region': prefs.get('domestic_or_international', {}).get('region', '')
                    }

                # Determine top_n based on category - more for beaches
                top_n = 30 if selected_category.lower() == 'beach' else 20

                collab_recommendations = recommender.recommend_for_user(
                    user_profile.custom_user_id,
                    user_preferences=user_preferences,
                    top_n=top_n
                )
                if not collab_recommendations.empty:
                    print(f"Found {len(collab_recommendations)} hybrid recommendations")
                    for _, row in collab_recommendations.iterrows():
                        # Get destination by destination_id
                        try:
                            dest = Destinations.objects.get(destination_id=row['destination_id'])
                            rec_dict = {
                                'id': dest.id,
                                'name': dest.desName,
                                'location': dest.location.locationName if dest.location else 'Unknown',
                                'category': dest.category or 'General',
                                'rating': dest.rating or 0.0,
                                'address': dest.address or '',
                                'description': dest.description or '',
                                'price_range': dest.price_range or 'Contact for pricing',
                                'image_url': dest.get_thumbnail_url() or 'https://picsum.photos/seed/default/800/600',
                                'recommendation_type': 'hybrid',
                                'hybrid_score': row['hybrid_score'],
                                'collab_score': row.get('collab_score', 0),
                                'content_score': row.get('content_score', 0)
                            }
                            collaborative_recommendations.append(rec_dict)
                            recommendations_list.append(rec_dict)
                            print(f"Added hybrid rec: {rec_dict['name']} (hybrid_score: {row['hybrid_score']:.3f})")
                        except Destinations.DoesNotExist:
                            print(f"Destination {row['destination_id']} not found in DB")
                            continue
        except Exception as e:
            print(f"Hybrid recommendation failed: {e}")

    # Always get search results from database (content-based)
    # Start with all destinations from database
    destinations_query = Destinations.objects.all().select_related('location')

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
    elif request.session.get('trip_destination'):
        # Fall back to trip destination from trip planner
        trip_destination = request.session.get('trip_destination', '').strip()
        if trip_destination:
            # Try to match as location name first
            destinations_query = destinations_query.filter(
                location__locationName__icontains=trip_destination
            )
            # If no results, it will fall through to show all (which is fine)

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
    elif not collaborative_recommendations and request.user.is_authenticated:
        # No collaborative recs and no filters - infer preferences from user's search history
        try:
            from .models import SearchHistory
            user_profile = UsersProfile.objects.filter(user=request.user).first()
            if user_profile:
                # Get user's recent search history
                recent_searches = SearchHistory.objects.filter(
                    user_id=user_profile.custom_user_id
                ).order_by('-timestamp')[:10]
                
                if recent_searches:
                    # Get categories from recent searches
                    searched_dest_ids = [s.destination_id for s in recent_searches]
                    searched_categories = Destinations.objects.filter(
                        destination_id__in=searched_dest_ids
                    ).values_list('category', flat=True).distinct()
                    
                    if searched_categories:
                        # Use the most common category from recent searches
                        from collections import Counter
                        category_counts = Counter(searched_categories)
                        inferred_category = category_counts.most_common(1)[0][0]
                        destinations_query = destinations_query.filter(category__icontains=inferred_category)
                        print(f"Inferred category from search history: {inferred_category}")
        except Exception as e:
            print(f"Error inferring preferences from search history: {e}")

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

    # Sort by rating (highest first) for content-based
    search_results_query = destinations_query.order_by('-rating')

    # Convert to list of dicts for template
    for dest in search_results_query:
        search_dict = {
            'id': dest.id,
            'name': dest.desName,
            'location': dest.location.locationName if dest.location else 'Unknown',
            'category': dest.category or 'General',
            'rating': dest.rating or 0.0,
            'address': dest.address or '',
            'description': dest.description or '',
            'price_range': dest.price_range or 'Contact for pricing',
            'image_url': dest.get_thumbnail_url() or 'https://picsum.photos/seed/default/800/600',
            'recommendation_type': 'search_result',
            'similarity_score': None
        }
        search_results.append(search_dict)
        # Add to main list if no collaborative or to show all
        if not collaborative_recommendations:
            recommendations_list.append(search_dict)

    # Sort collaborative recommendations by similarity score, content-based by rating
    if recommendations_list and recommendations_list[0].get('recommendation_type') == 'collaborative':
        recommendations_list.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    else:
        recommendations_list.sort(key=lambda x: x.get('rating', 0), reverse=True)

    # Check if any filters are applied
    filters_applied = bool(selected_location or selected_category or selected_price or selected_rating)

    # Always implement pagination for search results
    page_size = 15 if selected_category.lower() == 'beach' else 10
    if not collaborative_recommendations:
        # No collaborative recommendations - paginate all search results
        paginator = Paginator(search_results, page_size)
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)

        paginated_results = page_obj.object_list
        total_results = len(search_results)
        collaborative_recommendations = []  # Ensure it's empty
    else:
        # Have collaborative recommendations - show them first, then paginate remaining
        collab_count = 15 if selected_category.lower() == 'beach' else 10
        collaborative_recommendations = recommendations_list[:collab_count]  # Top N collaborative
        remaining_results = recommendations_list[collab_count:]  # Rest for pagination
        
        if remaining_results:
            paginator = Paginator(remaining_results, page_size)
            page_number = request.GET.get('page', 1)
            try:
                page_number = int(page_number)
            except ValueError:
                page_number = 1

            try:
                page_obj = paginator.page(page_number)
            except:
                page_obj = paginator.page(1)

            paginated_results = page_obj.object_list
            total_results = len(remaining_results)
        else:
            paginated_results = []
            page_obj = None
            total_results = 0

    # Get all locations and categories for filter dropdowns
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None values

    context = {
        'recommendations': recommendations_list,
        'collaborative_recommendations': collaborative_recommendations,
        'search_results': paginated_results,
        'user_preferences': user_data,
        'all_locations': all_locations,
        'all_categories': all_categories,
        'selected_location': selected_location,
        'selected_category': selected_category,
        'selected_price': selected_price,
        'selected_rating': selected_rating,
        'total_results': total_results,
        'page_obj': page_obj,
        'filters_applied': filters_applied,
        'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
    }

    return render(request, 'recommendResult.html', context)

@login_required
def user_profile(request):
    # 1. Lấy danh sách chuyến đi của user
    trips = Trip.objects.filter(user=request.user).order_by('-updated_at')
    
    # 2. Tìm ảnh đại diện xịn cho từng chuyến đi
    for trip in trips:
        # Mặc định dùng ảnh random nếu không tìm thấy gì
        trip.display_image = f"https://picsum.photos/seed/{trip.destination}/800/400"
        
        if trip.destination:
            search_term = trip.destination.strip()
            
            # --- ƯU TIÊN 1: Tìm theo tên chính xác của Địa điểm (Destinations) ---
            # Ví dụ: Trip to "Ba Na Hills" -> Tìm Destination "Ba Na Hills"
            dest = Destinations.objects.filter(desName__icontains=search_term).first()
            if dest:
                # data.csv dùng cột 'image_urls' (nhiều ảnh ngăn cách bởi |||)
                images = dest.get_image_list() 
                if images:
                    trip.display_image = images[0] # Lấy ảnh đầu tiên
                elif dest.image_url:
                    trip.display_image = dest.image_url
                continue # Đã tìm thấy, qua chuyến đi tiếp theo

            # --- ƯU TIÊN 2: Tìm theo tên chính xác của Khách sạn (Hotel) ---
            # Ví dụ: Trip to "Somerset Grand Hanoi"
            hotel = Hotel.objects.filter(name__icontains=search_term).first()
            if hotel and hotel.image_url:
                trip.display_image = hotel.image_url # hotels.csv dùng cột 'Image' -> model 'image_url'
                continue

            # --- ƯU TIÊN 3: Tìm theo Tên Thành Phố/Khu vực (Location) ---
            # Ví dụ: Trip to "Hanoi" -> Tìm đại một địa điểm bất kỳ thuộc Location "Hanoi" để lấy ảnh
            dest_in_loc = Destinations.objects.filter(location__locationName__icontains=search_term).first()
            if dest_in_loc:
                images = dest_in_loc.get_image_list()
                if images:
                    trip.display_image = images[0]
                elif dest_in_loc.image_url:
                    trip.display_image = dest_in_loc.image_url
                continue
            
            # Nếu không có Destination nào ở đó, thử tìm Hotel ở đó
            hotel_in_loc = Hotel.objects.filter(location__locationName__icontains=search_term).first()
            if hotel_in_loc and hotel_in_loc.image_url:
                trip.display_image = hotel_in_loc.image_url
                continue

    # 3. Lấy user preferences từ session
    user_data = request.session.get('user_preferences', None)
    
    # 4. Lấy tất cả categories để hiển thị trong select
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().exclude(category__isnull=True).order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None/empty values

    context = {
        'trips': trips,
        'user_preferences': user_data,
        'all_categories': all_categories,
    }
    return render(request, 'userProfile.html', context)

@login_required
def delete_trip(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id, user=request.user)
        # Delete associated TripItems first
        TripItem.objects.filter(trip=trip).delete()
        # Then delete the trip
        trip.delete()
        messages.success(request, 'Trip deleted successfully.')
    except Trip.DoesNotExist:
        messages.error(request, 'Trip not found.')
    
    return redirect('user_profile')

@login_required
def clear_history(request):
    if request.method == 'POST':
        # Clear SearchHistory for the user
        SearchHistory.objects.filter(user_id=request.user.usersprofile.custom_user_id).delete()
        messages.success(request, 'Search history cleared successfully.')
    return redirect('user_profile')

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

def destination_detail(request, destination_id):
    """View to display detailed information about a specific destination"""
    try:
        destination = Destinations.objects.select_related('location').get(id=destination_id)
        
        # Handle comment submission
        if request.method == 'POST' and request.user.is_authenticated:
            content = request.POST.get('content', '').strip()
            rating = request.POST.get('rating', '0')
            
            if content:
                Comment.objects.create(
                    user=request.user,
                    destination=destination,
                    content=content
                )
                messages.success(request, 'Your comment has been added!')
                
                # Handle rating submission
                if rating and rating != '0':
                    try:
                        rating_value = int(rating)
                        if 1 <= rating_value <= 5:
                            # Update or create user rating
                            user_rating, created = UserRating.objects.update_or_create(
                                user=request.user,
                                destination=destination,
                                defaults={'rating': rating_value}
                            )
                            if created:
                                messages.success(request, f'Your {rating_value}-star rating has been saved!')
                            else:
                                messages.success(request, f'Your rating has been updated to {rating_value} stars!')
                    except (ValueError, TypeError):
                        pass
                
                # Update user preference score after commenting
                from .Services.search_history_utils import update_user_preference_score
                update_user_preference_score(request.user, destination)
                return redirect('destination_detail', destination_id=destination_id)
            else:
                messages.error(request, 'Comment cannot be empty.')
        
        # Update user preference score based on actions (viewing destination)
        if request.user.is_authenticated:
            from .Services.search_history_utils import update_user_preference_score
            update_user_preference_score(request.user, destination)
        
        # Get hotels in the same location
        hotels = Hotel.objects.filter(location=destination.location).order_by('-rating')
        
        # Get comments for this destination
        comments = Comment.objects.filter(destination=destination).select_related('user')
        
        # Add rating to each comment
        for comment in comments:
            try:
                user_rating_obj = UserRating.objects.get(user=comment.user, destination=destination)
                comment.user_rating = user_rating_obj.rating
            except UserRating.DoesNotExist:
                comment.user_rating = None
        
        # Get user's current rating for this destination
        user_rating = None
        if request.user.is_authenticated:
            try:
                user_rating_obj = UserRating.objects.get(user=request.user, destination=destination)
                user_rating = user_rating_obj.rating
            except UserRating.DoesNotExist:
                user_rating = None
        
        context = {
            'destination': destination,
            'hotels': hotels,
            'comments': comments,
            'user_rating': user_rating,
            'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
        }
        return render(request, 'detail_destination.html', context)
    except Destinations.DoesNotExist:
        messages.error(request, 'Destination not found.')
        return redirect('recommend_result')

def about_us(request):
    return render(request, 'About-us.html')

def contact_us(request):
    return render(request, 'Contact-us.html')

def trip_planner(request):
    # Check if loading a saved trip
    trip_id = request.GET.get('trip_id')
    if trip_id and request.user.is_authenticated:
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            # Load trip data into session
            request.session['trip_destination'] = trip.destination
            request.session['trip_start_date'] = trip.departure_date.isoformat() if trip.departure_date else None
            request.session['trip_end_date'] = trip.arrival_date.isoformat() if trip.arrival_date else None
            request.session['trip_budget'] = trip.budget
            request.session['trip_travelers'] = trip.travelers
            request.session['trip_id'] = trip.id
            request.session.modified = True
        except Trip.DoesNotExist:
            pass  # Ignore if trip not found

    # Lấy thông tin trip từ session
    destination_name = request.session.get('trip_destination', 'Your Destination')
    from datetime import datetime

    departure_raw = request.session.get('trip_start_date')
    arrival_raw = request.session.get('trip_end_date')

    departure_date = None
    arrival_date = None

    if departure_raw:
        try:
            departure_date = datetime.fromisoformat(departure_raw).date()
        except ValueError:
            departure_date = datetime.strptime(departure_raw, "%Y-%m-%d").date()

    if arrival_raw:
        try:
            arrival_date = datetime.fromisoformat(arrival_raw).date()
        except ValueError:
            arrival_date = datetime.strptime(arrival_raw, "%Y-%m-%d").date()


    # 1. Lấy Budget từ Session (mặc định là 50 triệu nếu chưa có)
    budget = request.session.get('trip_budget', 50) 
    travelers = request.session.get('trip_travelers', 1)

    # 2. Đảm bảo budget là con số để tránh lỗi hiển thị
    try:
        budget_display = float(budget)
    except (TypeError, ValueError):
        budget_display = 50.0

    # 3. Tính toán giá mỗi người
    price_per_person = round(budget_display / travelers, 2) if travelers > 0 else 0

    trip_map_url = request.session.get('trip_map_url', None)
    trip_image_url = request.session.get('trip_image_url', None)

    # Lấy danh sách địa điểm theo location
    destinations = Destinations.objects.none()  # Empty queryset by default
    
    if destination_name and destination_name != 'Your Destination':
        # Try to find destinations by location name
        try:
            destinations = Destinations.objects.filter(
                location__locationName__icontains=destination_name
            )[:20]  # Limit to 20 results
        except Exception as e:
            print(f"Error loading destinations: {e}")
            destinations = Destinations.objects.all()[:10]
    else:
        # Show random destinations if no trip destination set
        destinations = Destinations.objects.all().order_by('?')[:10]

    # Lấy các địa điểm đã lưu trong trip
    trip_items = []
    saved_items = []
    if request.user.is_authenticated:
        saved_items = TripItem.objects.filter(user=request.user, trip__isnull=True).select_related('destination', 'hotel')
        trip_items = TripItem.objects.filter(user=request.user, trip__isnull=False).select_related('destination', 'hotel')

    days = []
    num_days = 0
    date_range = ''

    if departure_date and arrival_date:
        date_range = f"{departure_date.strftime('%m/%d')} – {arrival_date.strftime('%m/%d')}"

        current = departure_date
        index = 1

        while current <= arrival_date:
            days.append({
                'index': index,
                'date': current,
                'weekday': current.strftime('%A'),
                'label': current.strftime('%a %m/%d')
            })
            current += timedelta(days=1)
            index += 1

        num_days = len(days)


    context = {
        'destinations': destinations,
        'trip_items': trip_items,
        'saved_items': saved_items,
        'trip_destination': destination_name,
        'departure_date': departure_date,
        'arrival_date': arrival_date,
        'budget': budget_display, # Số triệu (VD: 50.0)
        'travelers': travelers,
        'price_per_person': price_per_person,
        'trip_map_url': trip_map_url,
        'trip_image_url': trip_image_url,
        'days': days,
        'num_days': num_days,
        'date_range': date_range,
    }
    
    return render(request, 'Trip-planner.html', context)

def input_trip_planner(request):
    from django.utils.translation import gettext as _, get_language
    print(f"DEBUG: input_trip_planner called, language: {get_language()}")
    # Get all locations for destination dropdown
    all_locations = Location.objects.all().order_by('locationName')
    
    # Get current trip data from session
    budget = request.session.get('trip_budget', 50)
    travelers = request.session.get('trip_travelers', 1)
    destination = request.session.get('trip_destination', '')
    start_date = request.session.get('trip_start_date', '')
    end_date = request.session.get('trip_end_date', '')
    
    context = {
        'all_locations': all_locations,
        'page_title': _('Plan Your Trip'),
        'plan_new_trip': _('Plan a new trip'),
        'odyscape_logo': _('Odyscape Logo'),
        'or_write_guide': _('Or write a new guide'),
        'destination_label': _('Destination'),
        'budget': budget,
        'travelers': travelers,
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date,
    }
    print(f"DEBUG: context page_title: {context['page_title']}")
    return render(request, 'inputTripPlanner.html', context)

def trip_form(request):
    """Handle trip planning form submission"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to create a trip.')
            return redirect('login_page')
        
        # Get form data
        destination = request.POST.get('destination', '').strip()
        departure_date = request.POST.get('departure', '').strip()
        arrival_date = request.POST.get('arrival', '').strip()
        budget = request.POST.get('budget', 0)
        travelers = request.POST.get('travelers', 1)
        price_per_person = request.POST.get('price_per_person', '').strip()
        
        # Validate required fields
        if not destination:
            messages.error(request, 'Destination is required.')
            return redirect('input_trip_planner')
        
        try:
            # Convert budget to integer
            budget = int(budget) if budget else 0
            travelers = int(travelers) if travelers else 1
            
            # Parse dates if provided
            departure = None
            arrival = None
            if departure_date:
                try:
                    departure = datetime.strptime(departure_date, '%d/%m/%Y').date()
                except ValueError:
                    messages.warning(request, 'Invalid departure date format. Use DD/MM/YYYY.')
            
            if arrival_date:
                try:
                    arrival = datetime.strptime(arrival_date, '%d/%m/%Y').date()
                except ValueError:
                    messages.warning(request, 'Invalid arrival date format. Use DD/MM/YYYY.')
            
            # Create trip
            trip = Trip.objects.create(
                user=request.user,
                destination=destination,
                departure_date=departure,
                arrival_date=arrival,
                budget=budget,
                travelers=travelers,
                price_per_person=price_per_person if price_per_person else None
            )
            
            # Store trip data in session for trip planner
            request.session['trip_destination'] = destination
            request.session['trip_start_date'] = departure.isoformat() if departure else None
            request.session['trip_end_date'] = arrival.isoformat() if arrival else None
            request.session['trip_budget'] = budget
            request.session['trip_travelers'] = travelers
            request.session['trip_price_per_person'] = price_per_person
            
            # Store trip ID for itinerary API
            request.session['trip_id'] = trip.id
            
            # Google Map URL
            request.session['trip_map_url'] = f"https://maps.google.com/maps?output=embed&q={destination}&z=12"

            # Lấy hình ảnh ngẫu nhiên cho location
            destinations_for_location = Destinations.objects.filter(location__locationName=destination)
            hotels_for_location = Hotel.objects.filter(location__locationName=destination)

            all_images = list(destinations_for_location.values_list('image_url', flat=True)) + \
                        list(hotels_for_location.values_list('image_url', flat=True))

            if all_images:
                trip_image = random.choice(all_images)
            else:
                trip_image = '/static/images/default_trip_image.png'

            request.session['trip_image_url'] = trip_image

            messages.success(request, f'Trip to {destination} has been created successfully!')
            return redirect('trip_planner')
            
        except Exception as e:
            messages.error(request, f'Error creating trip: {str(e)}')
            return redirect('input_trip_planner')
    
    # GET request - redirect to input form
    return redirect('input_trip_planner')


@csrf_exempt
def update_trip_settings(request):
    if request.method == 'POST':
        try:
            travelers = request.POST.get('travelers')
            budget = request.POST.get('budget')
            trip_type = request.POST.get('trip_type')

            from datetime import datetime

            start_date_raw = request.POST.get('start_date')
            end_date_raw = request.POST.get('end_date')

            if start_date_raw:
                start_date = datetime.strptime(start_date_raw, "%d/%m/%Y").date()
                request.session['trip_start_date'] = start_date.isoformat()

            if end_date_raw:
                end_date = datetime.strptime(end_date_raw, "%d/%m/%Y").date()
                request.session['trip_end_date'] = end_date.isoformat()

            if travelers:
                request.session['trip_travelers'] = int(travelers)
            if budget:
                request.session['trip_budget'] = int(budget)
            if trip_type:
                request.session['trip_type'] = trip_type

            request.session.modified = True

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False})

@csrf_exempt
def add_to_trip(request, destination_id):
    """Add destination to user's trip list - For Trip Planner page"""
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please login to add destinations to your trip.'})
        messages.error(request, 'Please login to add destinations to your trip.')
        return redirect('login_page')
    
    if request.method == 'POST':
        try:
            destination = Destinations.objects.get(id=destination_id)
            trip_item, created = TripItem.objects.get_or_create(
                user=request.user,
                destination=destination
            )
            if created:
                messages.success(request, f'Added {destination.desName} to your trip!')
                # Update user preference score after adding to trip
                from .Services.search_history_utils import update_user_preference_score
                update_user_preference_score(request.user, destination)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': f'Added {destination.desName} to your trip!', 
                        'item_id': trip_item.id,
                        'name': destination.desName,
                        'address': destination.address,
                        'price_range': destination.price_range
                    })
            else:
                messages.info(request, f'{destination.desName} is already in your trip.')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': f'{destination.desName} is already in your trip.'})
        except Destinations.DoesNotExist:
            messages.error(request, 'Destination not found.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Destination not found.'})
        except Exception as e:
            print(f"Error in add_to_trip: {e}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred while adding to trip.'})
            messages.error(request, 'An error occurred while adding to trip.')
    
    # Always return HttpResponse - redirect to previous page or trip planner
    return redirect(request.META.get('HTTP_REFERER', 'trip_planner'))

@csrf_exempt
def add_destination_to_trip(request, destination_id):
    """Add destination to user's trip list - For other pages (detail, recommend, etc.)"""
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please login to add destinations to your trip.'})
        messages.error(request, 'Please login to add destinations to your trip.')
        return redirect('login_page')
    
    try:
        destination = Destinations.objects.get(id=destination_id)
        trip_item, created = TripItem.objects.get_or_create(
            user=request.user,
            destination=destination
        )
        
        if created:
            messages.success(request, f'Added {destination.desName} to your trip!')
            # Update user preference score
            try:
                from .Services.search_history_utils import update_user_preference_score
                update_user_preference_score(request.user, destination)
            except:
                pass
            
            # Return JSON for AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Added {destination.desName} to your trip!',
                    'item_id': trip_item.id,
                    'item_name': destination.desName
                })
        else:
            messages.info(request, f'{destination.desName} is already in your trip.')
            # Return JSON for AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'{destination.desName} is already in your trip.'
                })
            
    except Destinations.DoesNotExist:
        messages.error(request, 'Destination not found.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Destination not found.'})
    except Exception as e:
        print(f"Error in add_destination_to_trip: {e}")
        messages.error(request, 'An error occurred while adding to trip.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'An error occurred while adding to trip.'})
    
    # Redirect back to previous page for non-AJAX
    return redirect(request.META.get('HTTP_REFERER', 'recommend_result'))

def remove_from_trip(request, trip_item_id):
    """Remove destination from user's trip list"""
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please login to remove items.'})
        messages.error(request, 'Please login to manage your trip.')
        return redirect('login_page')
    
    try:
        trip_item = TripItem.objects.get(id=trip_item_id, user=request.user)
        
        if trip_item.destination:
            item_name = trip_item.destination.desName
        elif trip_item.hotel:
            item_name = trip_item.hotel.name
        else:
            item_name = "Unknown"
        
        trip_item.delete()
        
        # Return JSON for AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Removed {item_name} from your trip.',
                'item_name': item_name
            })
        
        # Redirect for non-AJAX requests
        messages.success(request, f'Removed {item_name} from your trip.')
        return redirect('trip_list')
        
    except TripItem.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Trip item not found.'})
        messages.error(request, 'Trip item not found.')
        return redirect('trip_list')

def add_hotel_to_trip(request, hotel_id):
    """Add hotel to user's trip list"""
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please login to add hotels to your trip.'})
        messages.error(request, 'Please login to add hotels to your trip.')
        return redirect('login_page')
    
    if request.method == 'POST':
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            trip_item, created = TripItem.objects.get_or_create(
                user=request.user,
                hotel=hotel
            )
            if created:
                messages.success(request, f'Added {hotel.name} to your trip!')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': f'Added {hotel.name} to your trip!', 
                        'item_id': trip_item.id,
                        'name': hotel.name,
                        'address': hotel.address,
                        'price_range': f"{hotel.price} VND/night" if hotel.price else "Contact for pricing"
                    })
            else:
                messages.info(request, f'{hotel.name} is already in your trip.')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': f'{hotel.name} is already in your trip.'})
        except Hotel.DoesNotExist:
            messages.error(request, 'Hotel not found.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Hotel not found.'})
        except Exception as e:
            print(f"Error in add_hotel_to_trip: {e}")
            traceback.print_exc()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred while adding to trip.'})
            messages.error(request, 'An error occurred while adding to trip.')
    
    # Always return HttpResponse - redirect to previous page or trip planner
    return redirect(request.META.get('HTTP_REFERER', 'trip_planner'))

def trip_list(request):
    """Display user's trip list"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view your trip list.')
        return redirect('login_page')
    
    trip_items = TripItem.objects.filter(user=request.user).select_related('destination', 'hotel')
    
    context = {
        'trip_items': trip_items,
        'total_items': trip_items.count(),
    }
    
    return render(request, 'trip_list.html', context)

@csrf_exempt
def save_day_selections(request):
    """Save selected items for a specific day"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login to save selections.'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            day = data.get('day')
            selected_items = data.get('selected_items', [])
            
            if not isinstance(day, int) or day < 1:
                return JsonResponse({'success': False, 'message': 'Invalid day.'})
            
            # Clear previous selections for this day
            TripItem.objects.filter(user=request.user, day=day).update(day=None)
            
            # Set day for selected items
            for item_id in selected_items:
                try:
                    trip_item = TripItem.objects.get(id=item_id, user=request.user)
                    trip_item.day = day
                    trip_item.save()
                except TripItem.DoesNotExist:
                    continue
            
            return JsonResponse({'success': True, 'message': f'Saved selections for day {day}.'})
        except Exception as e:
            print(f"Error saving day selections: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred while saving.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@csrf_exempt
@require_POST
def auto_fill_day(request):
    """Gợi ý các địa điểm cho một ngày trong trip"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login to use auto-fill.'})
    try:
        data = json.loads(request.body)
        day = data.get('day')
        # Lấy các địa điểm chưa được chọn cho ngày này
        trip_items = TripItem.objects.filter(user=request.user, day__isnull=True).select_related('destination')
        # Gợi ý: chọn ngẫu nhiên 2-3 địa điểm chưa chọn
        suggested = random.sample(list(trip_items), min(3, trip_items.count())) if trip_items.count() > 0 else []
        result = [
            {
                'id': item.id,
                'name': item.destination.desName if item.destination else '',
                'address': item.destination.address if item.destination else '',
                'image_url': item.destination.image_url if item.destination else ''
            }
            for item in suggested
        ]
        # Gán các item này vào ngày
        for item in suggested:
            item.day = day
            item.save()
        return JsonResponse({'success': True, 'suggested': result})
    except Exception as e:
        print(f"Error in auto_fill_day: {e}")
        return JsonResponse({'success': False, 'message': 'Error auto-filling day.'})

@csrf_exempt
@require_POST
def optimize_route(request):
    """Tối ưu thứ tự các địa điểm cho một ngày (ví dụ: theo rating)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login to optimize route.'})
    try:
        data = json.loads(request.body)
        day = data.get('day')
        # Lấy các địa điểm đã chọn cho ngày này
        trip_items = TripItem.objects.filter(user=request.user, day=day).select_related('destination')
        # Sắp xếp theo rating giảm dần
        sorted_items = sorted(trip_items, key=lambda x: x.destination.rating if x.destination else 0, reverse=True)
        result = [
            {
                'id': item.id,
                'name': item.destination.desName if item.destination else '',
                'address': item.destination.address if item.destination else '',
                'image_url': item.destination.image_url if item.destination else ''
            }
            for item in sorted_items
        ]
        return JsonResponse({'success': True, 'optimized': result})
    except Exception as e:
        print(f"Error in optimize_route: {e}")
        return JsonResponse({'success': False, 'message': 'Error optimizing route.'})

@login_required
@require_POST
def save_trip_api(request):
    try:
        data = json.loads(request.body)
        
       # 1. Tìm chuyến đi được cập nhật gần đây nhất của user này
        trip = Trip.objects.filter(user=request.user).order_by('-updated_at').first()

        # 2. Nếu chưa có chuyến nào thì tạo mới
        if not trip:
            trip = Trip.objects.create(
                user=request.user, 
                destination=data.get('title', 'My Trip')
            )

        # Cập nhật thông tin Trip
        trip.destination = data.get('title')
        
        # Xử lý Budget: Frontend slider thường trả về số nhỏ (vd: 10, 50 triệu)
        # Cần nhân lên nếu lưu DB là VND
        raw_budget = float(data.get('budget', 0))
        if raw_budget < 10000: # Nếu số nhỏ (<10.000), giả định là đơn vị Triệu
             trip.budget = raw_budget * 1000000
        else:
             trip.budget = raw_budget

        trip.travelers = int(data.get('travelers', 1))

        # Xử lý ngày tháng (Frontend gửi dd/mm/yyyy -> Cần chuyển về YYYY-MM-DD)
        date_fmt = "%d/%m/%Y"
        if data.get('start_date'):
            try:
                trip.departure_date = datetime.strptime(data.get('start_date'), date_fmt).date()
            except ValueError:
                pass
        if data.get('end_date'):
            try:
                trip.arrival_date = datetime.strptime(data.get('end_date'), date_fmt).date()
            except ValueError:
                pass
        
        trip.save()

        # 2. XỬ LÝ TRIP ITEMS (Danh sách địa điểm)
        items_data = data.get('items', [])
        
        with transaction.atomic():
            for item in items_data:
                dest_id = item.get('destination_id')
                day = item.get('day')
                order = item.get('order')
                notes = item.get('notes', '')

                if dest_id:
                    # Dùng update_or_create để đảm bảo item được cập nhật đúng ngày/thứ tự
                    TripItem.objects.update_or_create(
                        user=request.user,
                        destination_id=dest_id,
                        defaults={
                            'day': day,
                            'order': order,
                            'notes': notes
                        }
                    )

        return JsonResponse({'success': True, 'message': 'Trip saved successfully!'})

    except Exception as e:
        print(f"Error saving trip: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def update_profile_settings(request):
    """Xử lý lưu thông tin từ trang User Profile"""
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ form
        username = request.user.username
        region = request.POST.get('region')
        budget = request.POST.get('budget')
        departure_date = request.POST.get('departure_date')
        return_date = request.POST.get('return_date')
        num_people = request.POST.get('num_people', 1)
        tags = request.POST.getlist('tags', [])
        favourite_destination_type = request.POST.get('favourite_destination_type')
        
        # 2. Cập nhật UsersProfile nếu có favourite_destination_type
        if favourite_destination_type:
            try:
                user_profile = UsersProfile.objects.get(user=request.user)
                user_profile.favourite_destination_type = favourite_destination_type
                user_profile.save()
                messages.success(request, f'✅ Favourite destination type updated to: {favourite_destination_type}')
            except UsersProfile.DoesNotExist:
                messages.error(request, 'User profile not found.')
                return redirect('user_profile')
        
        # 3. Tạo cấu trúc JSON cho session
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
                "num_people": int(num_people) if num_people else 1,
                "favourite_destination_type": favourite_destination_type
            }
        }
        
        # 4. Lưu vào Session
        request.session['user_preferences'] = user_data
        request.session.modified = True
        
        # 5. Lưu file JSON (Optional)
        try:
            input_folder = os.path.join('sightseeing', 'Services', 'user_inputs')
            os.makedirs(input_folder, exist_ok=True)
            filename = f"user_input_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(input_folder, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving JSON: {e}")

        # 6. Thông báo và Quay lại trang Profile
        messages.success(request, '✅ Profile settings updated successfully!')
        return redirect('user_profile')
    
    return redirect('user_profile')

def recommend_result(request):
    """View for displaying recommended destinations with filtering and pagination"""
    from .models import Location, Destinations
    from django.core.paginator import Paginator
    from .Services.recommender import get_recommender
    
    # Get all locations and categories for filters
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().exclude(category__isnull=True).order_by('category')
    
    # Get filter parameters from GET request
    selected_location = request.GET.get('location', '')
    if selected_location:
        try:
            selected_location = int(selected_location)
        except ValueError:
            selected_location = ''
    selected_category = request.GET.get('category', '')
    selected_rating = request.GET.get('rating', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    destinations = Destinations.objects.all().order_by('-rating')
    
    # Apply filters
    if selected_location:
        destinations = destinations.filter(location_id=selected_location)
    
    if selected_category:
        destinations = destinations.filter(category=selected_category)
    
    if selected_rating:
        try:
            min_rating = float(selected_rating)
            destinations = destinations.filter(rating__gte=min_rating)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(destinations, 10)  # 10 per page
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)
    
    search_results = page_obj.object_list
    total_results = destinations.count()
    
    # Get top results (highest rated, limited to 3)
    top_results = Destinations.objects.all().order_by('-rating')[:3]
    
    # Get collaborative recommendations using the recommender service
    collaborative_recommendations = []
    try:
        recommender = get_recommender()
        if request.user.is_authenticated:
            # Get user-specific recommendations
            user_recs = recommender.recommend_for_user(
                request.user.username, 
                user_preferences={'category': selected_category or None},
                top_n=5
            )
            if not user_recs.empty:
                # Convert to dict format expected by template
                for _, row in user_recs.iterrows():
                    dest = Destinations.objects.filter(desName=row['name']).first()
                    if dest:
                        collaborative_recommendations.append({
                            'id': dest.id,
                            'name': dest.desName,
                            'location': dest.location.locationName if dest.location else '',
                            'rating': dest.rating or 0,
                            'price': getattr(dest, 'price', 500),
                            'image_url': dest.get_thumbnail_url() or '/static/images/placeholder.jpg'
                        })
        else:
            # For anonymous users, show top rated destinations
            top_dests = Destinations.objects.filter(rating__gte=4.0).order_by('-rating')[:5]
            for dest in top_dests:
                collaborative_recommendations.append({
                    'id': dest.id,
                    'name': dest.desName,
                    'location': dest.location.locationName if dest.location else '',
                    'rating': dest.rating or 0,
                    'price': getattr(dest, 'price', 500),
                    'image_url': dest.get_thumbnail_url() or '/static/images/placeholder.jpg'
                })
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        # Fallback: show top rated
        top_dests = Destinations.objects.filter(rating__gte=4.0).order_by('-rating')[:5]
        for dest in top_dests:
            collaborative_recommendations.append({
                'id': dest.id,
                'name': dest.desName,
                'location': dest.location.locationName if dest.location else '',
                'rating': dest.rating or 0,
                'price': getattr(dest, 'price', 500),
                'image_url': dest.get_thumbnail_url() or '/static/images/placeholder.jpg'
            })
    
    # Prepare search_results in the same format
    formatted_search_results = []
    for dest in search_results:
        formatted_search_results.append({
            'id': dest.id,
            'name': dest.desName,
            'location': dest.location.locationName if dest.location else '',
            'rating': dest.rating or 0,
            'price': getattr(dest, 'price', 500),
            'image_url': dest.get_thumbnail_url() or '/static/images/placeholder.jpg',
            'reviews_count': '2k+'  # Placeholder
        })
    
    # Prepare top_results
    formatted_top_results = []
    for dest in top_results:
        formatted_top_results.append({
            'id': dest.id,
            'name': dest.desName,
            'location': dest.location.locationName if dest.location else '',
            'rating': dest.rating or 0,
            'price': getattr(dest, 'price', 500),
            'image_url': dest.get_thumbnail_url() or '/static/images/placeholder.jpg',
            'reviews_count': '2k+'
        })
    
    context = {
        'all_locations': all_locations,
        'all_categories': all_categories,
        'selected_location': selected_location,
        'selected_category': selected_category,
        'selected_rating': selected_rating,
        'top_results': formatted_top_results,
        'collaborative_recommendations': collaborative_recommendations,
        'search_results': formatted_search_results,
        'page_obj': page_obj,
        'total_results': total_results,
        'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
        'LANGUAGE_CODE': request.LANGUAGE_CODE,
    }
    
    return render(request, 'recommendResult.html', context)

@csrf_exempt
def chat_api(request):
    """API xử lý chat cho cả Homepage và Trip Planner"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            request_type = data.get('type', 'general') # Phân biệt nguồn gọi: 'tripplanner' hay 'general'
            
            reply_text = ""

            # --- LOGIC CHO TRIP PLANNER (Có ngữ cảnh chuyến đi) ---
            if request_type == 'tripplanner':
                destination = data.get('destination', 'Unknown')
                budget = data.get('budget', '0')
                travelers = data.get('travelers', '1')
                date_range = data.get('date_range', '')

                # Logic trả lời giả lập (Bạn có thể thay bằng gọi API OpenAI/Gemini thật ở đây)
                if "gợi ý" in user_message or "suggest" in user_message:
                    reply_text = f"Vì bạn đi {destination} với ngân sách {budget} triệu cho {travelers} người, tôi gợi ý các địa điểm tham quan miễn phí như công viên thành phố hoặc bảo tàng địa phương."
                elif "ăn" in user_message or "food" in user_message:
                    reply_text = f"Tại {destination} có rất nhiều món ngon. Với nhóm {travelers} người, bạn nên đặt bàn trước tại các nhà hàng địa phương."
                elif "lịch trình" in user_message or "itinerary" in user_message:
                    reply_text = f"Lịch trình từ {date_range} có vẻ khá thoải mái. Bạn có muốn tôi sắp xếp lại thứ tự các điểm đến để tối ưu đường đi không?"
                else:
                    reply_text = f"Tôi thấy bạn đang lên kế hoạch đi {destination}. Bạn cần giúp gì cụ thể về ngân sách hay địa điểm không?"

            # --- LOGIC CHO HOMEPAGE (Chat chung) ---
            else:
                if "hello" in user_message or "chào" in user_message:
                    reply_text = "Chào bạn! Tôi là trợ lý ảo SmartTour. Bạn dự định đi du lịch ở đâu sắp tới?"
                elif "đà nẵng" in user_message:
                    reply_text = "Đà Nẵng là thành phố tuyệt vời! Chúng tôi có nhiều khách sạn và điểm tham quan hấp dẫn tại đó."
                else:
                    reply_text = "Tôi có thể giúp bạn tìm điểm đến, lên kế hoạch chuyến đi và dự trù kinh phí. Hãy hỏi tôi bất cứ điều gì!"

            return JsonResponse({'success': True, 'reply': reply_text})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
