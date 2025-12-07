from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
import json
import os
from datetime import datetime, timedelta
from .Services.recommender import get_recommender
from django.core.paginator import Paginator

from sightseeing.models import Destinations, Hotel
import random

from django.http import JsonResponse
from datetime import datetime

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
    # Get all locations and categories for filter dropdowns
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None values
    
    # Get personalized recommendations for authenticated users
    personalized_recommendations = []
    if request.user.is_authenticated:
        try:
            recommender = get_recommender()
            user_profile = UsersProfile.objects.filter(user=request.user).first()
            if user_profile and user_profile.custom_user_id:
                collab_recommendations = recommender.recommend_for_user(user_profile.custom_user_id, top_n=6)
                if not collab_recommendations.empty:
                    print(f"Found {len(collab_recommendations)} personalized recommendations for homepage")
                    for _, row in collab_recommendations.iterrows():
                        try:
                            dest = Destinations.objects.get(destination_id=row['destination_id'])
                            rec_dict = {
                                'id': dest.id,
                                'name': dest.desName,
                                'location': dest.location.locationName if dest.location else 'Unknown',
                                'category': dest.category or 'General',
                                'rating': dest.rating or 0.0,
                                'image_url': dest.image_url or 'https://picsum.photos/seed/default/400/300',
                                'similarity_score': row['similarity_score']
                            }
                            personalized_recommendations.append(rec_dict)
                        except Destinations.DoesNotExist:
                            continue
        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
    
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
                            'image_url': dest.image_url or 'https://picsum.photos/seed/default/400/300',
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
    
    if request.method == "POST":
        form = registerForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Auto-create UsersProfile with custom_user_id
            from .models import UsersProfile
            # Generate next user ID
            existing_profiles = UsersProfile.objects.all().order_by('-id')
            next_id = 1
            if existing_profiles:
                # Extract number from last custom_user_id (format: user_XXX)
                last_profile = existing_profiles.first()
                if last_profile.custom_user_id and last_profile.custom_user_id.startswith('user_'):
                    try:
                        last_num = int(last_profile.custom_user_id.split('_')[1])
                        next_id = last_num + 1
                    except (ValueError, IndexError):
                        next_id = existing_profiles.count() + 1
            
            UsersProfile.objects.create(
                user=user,
                name=form.cleaned_data.get('first_name', '') + ' ' + form.cleaned_data.get('last_name', ''),
                email=form.cleaned_data.get('email'),
                custom_user_id=f"user_{next_id:03d}"
            )
            
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
                collab_recommendations = recommender.recommend_for_user(user_profile.custom_user_id, top_n=20)
                if not collab_recommendations.empty:
                    print(f"Found {len(collab_recommendations)} collaborative recommendations")
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
                                'image_url': dest.image_url or 'https://picsum.photos/seed/default/800/600',
                                'recommendation_type': 'collaborative',
                                'similarity_score': row['similarity_score']
                            }
                            collaborative_recommendations.append(rec_dict)
                            recommendations_list.append(rec_dict)
                            print(f"Added collaborative rec: {rec_dict['name']} (type: {rec_dict['recommendation_type']})")
                        except Destinations.DoesNotExist:
                            print(f"Destination {row['destination_id']} not found in DB")
                            continue
        except Exception as e:
            print(f"Collaborative filtering failed: {e}")

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
            'image_url': dest.image_url or 'https://picsum.photos/seed/default/800/600',
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

    # Implement pagination
    if not filters_applied:
        # No filters applied - show 20 per page
        paginator = Paginator(recommendations_list, 20)
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)

        recommendations = page_obj.object_list
        total_results = len(recommendations_list)
    else:
        # Filters applied - show all results (no pagination for filtered results)
        recommendations = recommendations_list
        page_obj = None
        total_results = len(recommendations_list)

    # Get all locations and categories for filter dropdowns
    all_locations = Location.objects.all().order_by('locationName')
    all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
    all_categories = [cat for cat in all_categories if cat]  # Remove None values

    context = {
        'recommendations': recommendations_list,
        'collaborative_recommendations': collaborative_recommendations,
        'search_results': search_results,
        'user_preferences': user_data,
        'all_locations': all_locations,
        'all_categories': all_categories,
        'selected_location': selected_location,
        'selected_category': selected_category,
        'selected_price': selected_price,
        'selected_rating': selected_rating,
        'total_results': len(recommendations_list),
        'page_obj': page_obj,
        'filters_applied': filters_applied,
        'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
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

def destination_detail(request, destination_id):
    """View to display detailed information about a specific destination"""
    try:
        destination = Destinations.objects.select_related('location').get(id=destination_id)
        
        # Handle comment submission
        if request.method == 'POST' and request.user.is_authenticated:
            content = request.POST.get('content', '').strip()
            if content:
                Comment.objects.create(
                    user=request.user,
                    destination=destination,
                    content=content
                )
                messages.success(request, 'Your comment has been added!')
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
        
        context = {
            'destination': destination,
            'hotels': hotels,
            'comments': comments,
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
    # Get trip data from session
    destination = request.session.get('trip_destination', 'Unknown')
    departure_date = request.session.get('trip_departure', '')
    arrival_date = request.session.get('trip_arrival', '')
    budget = request.session.get('trip_budget', 0)
    travelers = request.session.get('trip_travelers', 1)
    price_per_person = request.session.get('trip_price_per_person', '')
    
    recommendations = Destinations.objects.filter(location__locationName__icontains=destination)

    # Calculate number of days
    num_days = 7  # default
    days = []
    date_range = ''
    if departure_date and arrival_date:
        try:
            dep = datetime.strptime(departure_date, '%d/%m/%Y').date()
            arr = datetime.strptime(arrival_date, '%d/%m/%Y').date()
            num_days = (arr - dep).days + 1
            if num_days < 1:
                num_days = 1
            date_range = f"{dep.strftime('%m/%d')} – {arr.strftime('%m/%d')}"
            for i in range(num_days):
                day_date = dep + timedelta(days=i)
                day_name = day_date.strftime('%A')
                day_short = day_date.strftime('%m/%d')
                full_name = f"{day_name}, {day_date.strftime('%B %d')}"
                days.append({
                    'date': day_date,
                    'day_name': day_name,
                    'day_short': day_short,
                    'full_name': full_name
                })
        except:
            num_days = 7
    
    # Ensure integers
    try:
        budget = int(budget) if budget else 0
    except:
        budget = 0
    try:
        travelers = int(travelers) if travelers else 1
    except:
        travelers = 1
    
    # Get personalized recommendations for authenticated users
    personalized_recommendations = []
    if request.user.is_authenticated:
        try:
            recommender = get_recommender()
            user_profile = UsersProfile.objects.filter(user=request.user).first()
            if user_profile and user_profile.custom_user_id:
                collab_recommendations = recommender.recommend_for_user(user_profile.custom_user_id, top_n=6)
                if not collab_recommendations.empty:
                    print(f"Found {len(collab_recommendations)} personalized recommendations for trip planner")
                    for _, row in collab_recommendations.iterrows():
                        try:
                            dest = Destinations.objects.get(destination_id=row['destination_id'])
                            rec_dict = {
                                'id': dest.id,
                                'name': dest.desName,
                                'location': dest.location.locationName if dest.location else 'Unknown',
                                'category': dest.category or 'General',
                                'rating': dest.rating or 0.0,
                                'image_url': dest.image_url or 'https://picsum.photos/seed/default/400/300',
                                'price_range': dest.price_range or 'Contact for pricing'
                            }
                            personalized_recommendations.append(rec_dict)
                        except Destinations.DoesNotExist:
                            continue
        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
    
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
                            'image_url': dest.image_url or 'https://picsum.photos/seed/default/400/300',
                            'price_range': dest.price_range or 'Contact for pricing'
                        }
                        personalized_recommendations.append(rec_dict)
                    except Destinations.DoesNotExist:
                        continue
        except Exception as e:
            print(f"Error getting popular destinations: {e}")
    
    # Get user's trip items
    trip_items = []
    checked_state = {}
    for item in TripItem.objects.filter(user=request.user).select_related('destination', 'hotel'):
        if item.destination:
            name = item.destination.desName
            address = item.destination.address
            price_range = item.destination.price_range
        elif item.hotel:
            name = item.hotel.name
            address = item.hotel.address
            price_range = f"{item.hotel.price} VND/night" if item.hotel.price else "Contact for pricing"
        else:
            name = 'Unknown'
            address = ''
            price_range = ''
        trip_items.append({
            'id': item.id,
            'destination__desName': name,
            'destination__address': address,
            'destination__price_range': price_range
        })
        
        # Build checked state
        if item.day:
            if item.day not in checked_state:
                checked_state[item.day] = {}
            checked_state[item.day][trip_items.index(trip_items[-1])] = True
    
    import json
    trip_items_json = json.dumps(trip_items)
    checked_state_json = json.dumps(checked_state)
    recommendations_json = json.dumps(personalized_recommendations)
    
    recommended_list = []
    for d in recommendations:
        recommended_list.append({
            "id": d.id,
            "name": d.desName,
            "location": d.location.locationName if d.location else "Unknown",
            "category": d.category or "General",
            "rating": d.rating or 0.0,
            "image_url": d.image_url or "https://picsum.photos/seed/default/400/300",
            "price_range": d.price_range or ""
        })

    context = {
        'destination': destination,
        'departure_date': departure_date,
        'arrival_date': arrival_date,
        'budget': budget,
        'travelers': travelers,
        'price_per_person': price_per_person,
        'num_days': num_days,
        'days': days,
        'date_range': date_range,
        'trip_items': trip_items,
        'trip_items_json': trip_items_json,
        'checked_state_json': checked_state_json,
        'recommendations_json': recommendations_json,
        'explore_recommendations': recommended_list,
        'explore_recommendations_json': json.dumps(recommended_list),
    }
    
    destination_name = request.session.get('trip_destination', None)
    
    destinations = []
    if destination_name:
        # Lọc destination theo tên user chọn
        destinations = Destinations.objects.filter(location__locationName=destination_name)

    return render(request, 'Trip-planner.html', {
        'destinations': destinations,
        'trip_destination': destination_name,
        'trip_map_url': request.session.get('trip_map_url', None),
        'trip_image_url': request.session.get('trip_image_url', None),
        'trip_budget': request.session.get('trip_budget', None),
        'trip_travelers': request.session.get('trip_travelers', None),
        'trip_price_per_person': request.session.get('trip_price_per_person', None)
    })

def input_trip_planner(request):
    # Get all locations for destination dropdown
    all_locations = Location.objects.all().order_by('locationName')
    
    context = {
        'all_locations': all_locations,
    }
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
            request.session["trip_start"] = request.POST.get("start_date")
            request.session["trip_end"] = request.POST.get("end_date")
            request.session['trip_budget'] = budget
            request.session['trip_travelers'] = travelers
            request.session['trip_price_per_person'] = price_per_person
            
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
    """Update trip settings via AJAX"""
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            travelers = request.POST.get('travelers')
            budget = request.POST.get('budget')
            
            # Update session
            if travelers:
                request.session['trip_travelers'] = int(travelers)
            if budget:
                request.session['trip_budget'] = int(budget)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
def add_to_trip(request, destination_id):
    """Add destination to user's trip list"""
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
        except Exception as e:
            print(f"Error in add_to_trip: {e}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred while adding to trip.'})
            messages.error(request, 'An error occurred while adding to trip.')
    
    if not request.headers.get('x-requested-with'):
        return redirect(request.META.get('HTTP_REFERER', 'home'))

def remove_from_trip(request, trip_item_id):
    """Remove destination from user's trip list"""
    if request.user.is_authenticated:
        try:
            trip_item = TripItem.objects.get(id=trip_item_id, user=request.user)
            if trip_item.destination:
                item_name = trip_item.destination.desName
            elif trip_item.hotel:
                item_name = trip_item.hotel.name
            else:
                item_name = "Unknown"
            trip_item.delete()
            messages.success(request, f'Removed {item_name} from your trip.')
        except TripItem.DoesNotExist:
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
                # Update user preference score after adding to trip (for hotel, maybe lower score)
                # For now, skip or add to search history with hotel_id
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
            import traceback
            traceback.print_exc()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred while adding to trip.'})
            messages.error(request, 'An error occurred while adding to trip.')
    
    if not request.headers.get('x-requested-with'):
        return redirect(request.META.get('HTTP_REFERER', 'home'))

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

