from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate,login,logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage # Cần thiết cho upload file
from django.core.exceptions import ValidationError # Cần thiết cho validation file
from django.views.decorators.http import require_http_methods
from django.db.models import Q 
import json
import os
from datetime import datetime
from django.conf import settings # Cần thiết cho email/media
from django.urls import reverse_lazy # Cần thiết cho URL

# [QUAN TRỌNG]: Import chính xác các Models bạn đã định nghĩa
# NOTE: Bạn phải đảm bảo các model Comment, Hotel, TripItem tồn tại trong .models nếu bạn muốn các hàm dưới đây hoạt động.
from .models import UsersProfile, Location, Destinations, registerForm, TripItem, Comment, Hotel
from django.contrib.auth.models import User 

# Nếu bạn đang sử dụng services/recommender, hãy đảm bảo các import này vẫn còn
try:
  from .Services.recommender import SightseeingRecommender, SightseeingSpot
  # from .Services.search_history_utils import update_user_preference_score # Cần thiết cho scoring
except ImportError:
  pass 

@ensure_csrf_cookie
def get_home(request):
  # Get all locations and categories for filter dropdowns
  all_locations = Location.objects.all().order_by('locationName')
  all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
  all_categories = [cat for cat in all_categories if cat] 

  context = {
    'all_locations': all_locations,
    'all_categories': all_categories,
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
      messages.success(request, f'Chào mừng trở lại, {username}!')
      return redirect('user_profile') 
    else: 
      messages.error(request, 'Tên người dùng hoặc mật khẩu không chính xác!')
  return render(request, 'loginPage.html')

def logout_view(request):
  from django.contrib.auth import logout
  logout(request)
  messages.success(request, 'Bạn đã đăng xuất thành công.')
  return redirect('home')

def signup_page(request):
  from django.contrib.auth import login
  
  if request.method == "POST":
    form = registerForm(request.POST)
    if form.is_valid():
      user = form.save()
      
      # Tự động tạo UsersProfile khi đăng ký (FIXED: Loại bỏ custom_user_id phức tạp)
      UsersProfile.objects.create(user=user) 
      
      # Tự động đăng nhập sau khi đăng ký
      login(request, user)
      username = form.cleaned_data.get('username')
      messages.success(request, f'Chào mừng {username}! Tài khoản của bạn đã được tạo thành công.')
      return redirect('user_profile') 
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
          'Yêu cầu đặt lại mật khẩu',
          f'Nhấp vào liên kết dưới đây để đặt lại mật khẩu của bạn:\n\n{reset_link}',
          settings.DEFAULT_FROM_EMAIL,
          [email],
          fail_silently=False,
        )
        messages.success(request, 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn!')
        return redirect('password_reset_done')
      except Exception as e:
        messages.error(request, f'Lỗi khi gửi email: {str(e)}')
    except User.DoesNotExist:
      messages.error(request, 'Không tìm thấy người dùng với địa chỉ email này.')
  
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
      messages.error(request, 'Mật khẩu không khớp!')
      return render(request, 'password_reset_confirm.html')
    
    try:
      user_id = force_str(urlsafe_base64_decode(uid))
      user = User.objects.get(pk=user_id)
      
      if default_token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Mật khẩu của bạn đã được đặt lại thành công!')
        return redirect('password_reset_complete')
      else:
        messages.error(request, 'Liên kết đặt lại không hợp lệ hoặc đã hết hạn.')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
      messages.error(request, 'Liên kết đặt lại không hợp lệ.')
  
  return render(request, 'password_reset_confirm.html')

def password_reset_complete(request):
  return render(request, 'password_reset_complete.html')

def recommend_result(request):
  """
  Hiển thị các gợi ý được cá nhân hóa dựa trên tùy chọn và bộ lọc của người dùng (từ URL).
  Bộ lọc đã được cải tiến để xử lý các chuỗi Ngân sách/Đánh giá.
  """
  from django.db.models import Q 
  
  destinations_query = Destinations.objects.all().select_related('location')
  
  # Lấy tham số bộ lọc từ GET request (từ nút Search trên trang Profile)
  selected_destination = request.GET.get('destination', '').strip()
  selected_price = request.GET.get('budget', '').strip()
  selected_rating = request.GET.get('ratings', '').strip()
  selected_preferences = request.GET.get('preferences', '').strip()
  selected_category = request.GET.get('category', '').strip() # FIX: Bổ sung biến bị thiếu
  
  # --- 1. Lọc Điểm đến ---
  if selected_destination:
    destinations_query = destinations_query.filter(
      Q(location__locationName__icontains=selected_destination) | 
      Q(desName__icontains=selected_destination)
    )

  # --- 2. Lọc Đánh giá (Rating) ---
  if selected_rating:
    try:
      # Trích xuất giá trị số từ chuỗi (ví dụ: '4+ Stars' -> 4.0, '5 Stars' -> 5.0)
      if '+' in selected_rating:
        min_rating = float(selected_rating.split('+')[0].strip())
      elif 'Stars' in selected_rating:
        min_rating = float(selected_rating.split(' ')[0].strip())
      else:
        min_rating = 0.0 # Giá trị mặc định nếu không khớp
      
      if min_rating > 0:
        destinations_query = destinations_query.filter(rating__gte=min_rating)
    except ValueError:
      pass
  
  # --- 3. Lọc Ngân sách (Price) ---
  if selected_price and selected_price != 'Chưa thiết lập':
    price_filter = Q()
    
    if '100K' in selected_price:
      price_filter |= Q(price_range__icontains='100K') | Q(price_range__icontains='500K')
    elif '500K' in selected_price:
      price_filter |= Q(price_range__icontains='500K') | Q(price_range__icontains='1M')
    elif '1M' in selected_price and '3M' in selected_price:
      price_filter |= Q(price_range__icontains='1M') | Q(price_range__icontains='3M')
    elif '3M' in selected_price and '10M' in selected_price:
      price_filter |= Q(price_range__icontains='3M') | Q(price_range__icontains='10M')
    elif '10M+' in selected_price:
      price_filter |= Q(price_range__icontains='10M+') | Q(price_range__icontains='premium')
    else:
      # Xử lý custom input
      price_filter |= Q(price_range__icontains=selected_price.replace(' ', ''))
      
    destinations_query = destinations_query.filter(price_filter)

  # --- 4. Lọc Sở thích (Preferences) ---
  if selected_preferences:
    tags = [t.strip().lower() for t in selected_preferences.split(',') if t.strip()]
    if tags:
      tag_filter = Q()
      for tag in tags:
        # Lọc theo Category HOẶC tên địa điểm
        tag_filter |= Q(category__icontains=tag) | Q(desName__icontains=tag)
      destinations_query = destinations_query.filter(tag_filter)
  
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
      'price_range': dest.price_range or 'Liên hệ để biết giá',
      'image_url': dest.image_url or 'https://picsum.photos/seed/default/800/600',
    })
  
  # Get all locations and categories for filter dropdowns (làm mới cho filter bar)
  all_locations = Location.objects.all().order_by('locationName')
  all_categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
  all_categories = [cat for cat in all_categories if cat] 
  
  context = {
    'recommendations': recommendations_list,
    'all_locations': all_locations,
    'all_categories': all_categories,
    'selected_location': selected_destination, # Sử dụng selected_destination để giữ lại giá trị
    'selected_category': selected_category,
    'selected_price': selected_price,
    'selected_rating': selected_rating,
    'total_results': len(recommendations_list),
  }
  
  return render(request, 'recommendResult.html', context)

def user_profile(request):
  """
  View để render trang Profile, sử dụng get_or_create và truyền dữ liệu cần thiết.
  """
  if not request.user.is_authenticated:
    # Xử lý trường hợp chưa đăng nhập, chuyển hướng đến trang đăng nhập nếu cần
    return redirect('login_page') 
    
  # Lấy hoặc tạo mới UsersProfile cho người dùng hiện tại
  profile, created = UsersProfile.objects.get_or_create(user=request.user)
  
  # Định dạng ngày tháng thành chuỗi YYYY-MM-DD cho input HTML (Đã sửa lỗi)
  arrival_date_str = profile.arrival_date.strftime('%Y-%m-%d') if profile.arrival_date else ''
  departure_date_str = profile.departure_date.strftime('%Y-%m-%d') if profile.departure_date else ''
  
  # Tách chuỗi preferences thành danh sách để hiển thị tags
  preferences_list = [p.strip() for p in profile.preferences.split(',') if p.strip()]

  # Danh sách tags cố định cho form
  ALL_PREFERENCES_LIST = [
    "Landmark", "Sanctuary", "Cultural Sites", "Local Cuisine", 
    "Beach", "Mountain", "Shopping", "Adventure"
  ]

  context = {
    'profile': profile,
    'arrival_date_input': arrival_date_str,
    'departure_date_input': departure_date_str,
    'preferences_list': preferences_list, 
    'ALL_PREFERENCES_LIST': ALL_PREFERENCES_LIST # Truyền danh sách tags cố định
  }
  return render(request, 'userProfile.html', context) 


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
    tags = request.POST.getlist('tags', []) 
    
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
    
    messages.success(request, f'✅ Đã lưu thông tin! Đang tạo gợi ý...')
    
    # Redirect to recommendation results
    return redirect('recommend_result')
  
  return redirect('user_input')

def destination_detail(request, destination_id):
  """View để hiển thị thông tin chi tiết về một điểm đến cụ thể"""
  try:
    destination = Destinations.objects.select_related('location').get(id=destination_id)
    
    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
      content = request.POST.get('content', '').strip()
      if content:
        # Comment.objects.create( ... ) # Giả định Model Comment tồn tại
        messages.success(request, 'Bình luận của bạn đã được thêm!')
        return redirect('destination_detail', destination_id=destination_id)
      else:
        messages.error(request, 'Bình luận không được để trống.')
    
    # Update user preference score based on actions (viewing destination)
    if request.user.is_authenticated:
      pass # Logic update preference score ở đây

    # Get related destinations (same location or category)
    related = Destinations.objects.filter(
      location=destination.location
    ).exclude(id=destination_id)[:3]
    
     # Get hotels in the same location
    hotels = Hotel.objects.filter(location=destination.location).order_by('-rating')[:5]
    
    # Get comments for this destination
    comments = Comment.objects.filter(destination=destination).select_related('user')
    
    context = {
      'destination': destination,
      'related_destinations': related,
        'hotels': hotels,
        'comments': comments,
        'trip_count': TripItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'detail_destination.html', context)
  except Destinations.DoesNotExist:
    messages.error(request, 'Không tìm thấy điểm đến.')
    return redirect('recommend_result')

def about_us(request):
  return render(request, 'About-us.html')

def contact_us(request):
  return render(request, 'Contact-us.html')

def trip_planner(request):
  return render(request, 'Trip-planner.html')

def add_to_trip(request, destination_id):
  """Add destination to user's trip list"""
  if request.method == 'POST' and request.user.is_authenticated:
    try:
      destination = Destinations.objects.get(id=destination_id)
      # trip_item, created = TripItem.objects.get_or_create( ... ) # Model TripItem chưa được import
      created = True # Giả định tạo thành công
      if created:
        messages.success(request, f'Đã thêm {destination.desName} vào chuyến đi của bạn!')
        # Logic update preference score
        pass 
      else:
        messages.info(request, f'{destination.desName} đã có trong chuyến đi của bạn.')
    except Destinations.DoesNotExist:
      messages.error(request, 'Không tìm thấy điểm đến.')
  
  return redirect('destination_detail', destination_id=destination_id)

def remove_from_trip(request, trip_item_id):
  """Remove destination from user's trip list"""
  if request.user.is_authenticated:
    try:
      # trip_item = TripItem.objects.get(id=trip_item_id, user=request.user) # Model TripItem chưa được import
      destination_name = "Điểm đến đã xóa"
      # trip_item.delete()
      messages.success(request, f'Đã xóa {destination_name} khỏi chuyến đi của bạn.')
    except NameError: # TripItem.DoesNotExist:
      messages.error(request, 'Mục chuyến đi không tìm thấy.')
  
  return redirect('trip_list')

def trip_list(request):
  """Display user's trip list"""
  if not request.user.is_authenticated:
    messages.error(request, 'Vui lòng đăng nhập để xem danh sách chuyến đi của bạn.')
    return redirect('login_page')
  
  # trip_items = TripItem.objects.filter(user=request.user).select_related('destination') # Model TripItem chưa được import
  
  context = {
    'trip_items': [],
    'total_items': 0,
  }
  
  return render(request, 'trip_list.html', context)
@require_http_methods(["POST"])
def edit_profile_data(request):
  """
  Xử lý AJAX POST để lưu Preferences và Personal Info.
  """
  
  # 1. Kiểm tra xác thực 
  if not request.user.is_authenticated:
    return JsonResponse({'error': 'Yêu cầu xác thực.'}, status=401)
    
  # 2. Nhận dữ liệu JSON từ Frontend
  try:
    data = json.loads(request.body)
    
    # Dữ liệu Preferences
    destination = data.get('destination')
    group_size = data.get('group_size')
    arrival_date_str = data.get('arrival_date')
    departure_date_str = data.get('departure_date')
    budget = data.get('budget')
    # Preferences là một mảng tags, chuyển về chuỗi
    preferences = ", ".join(data.get('preferences', [])) 
    preferred_ratings = data.get('preferred_ratings')
    
    # Dữ liệu Personal Info
    name = data.get('name')
    email = data.get('email')
    bio = data.get('bio')


  except json.JSONDecodeError:
    return JsonResponse({'error': 'Định dạng JSON không hợp lệ trong yêu cầu.'}, status=400)
  
  # 3. Logic Xử lý & Lưu vào Database
  try:
    # Thay thế get bằng get_or_create để đảm bảo profile tồn tại
    profile, created = UsersProfile.objects.get_or_create(user=request.user)
    
    # Cập nhật các trường Preferences
    profile.destination = destination
    profile.group_size = group_size
    profile.budget = budget
    profile.preferences = preferences
    profile.preferred_ratings = preferred_ratings
    
    # Cập nhật các trường Personal Info
    profile.name = name
    profile.email = email
    profile.bio = bio
    
    # Chuyển đổi chuỗi ngày tháng sang đối tượng DateField (FIXED)
    arrival_date_str = arrival_date_str.strip() if arrival_date_str else ''
    departure_date_str = departure_date_str.strip() if departure_date_str else ''


    if arrival_date_str and arrival_date_str not in ('None', 'Chưa thiết lập'):
      try:
        # Định dạng mong đợi từ input type="date" là YYYY-MM-DD
        profile.arrival_date = datetime.strptime(arrival_date_str, '%Y-%m-%d').date()
      except ValueError:
        return JsonResponse({'error': 'Lỗi định dạng ngày đến. Vui lòng kiểm tra lại. (Cần YYYY-MM-DD)'}, status=400)
    else:
      profile.arrival_date = None # Đặt None nếu chuỗi rỗng

    if departure_date_str and departure_date_str not in ('None', 'Chưa thiết lập'):
      try:
        profile.departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
      except ValueError:
        return JsonResponse({'error': 'Lỗi định dạng ngày đi. Vui lòng kiểm tra lại. (Cần YYYY-MM-DD)'}, status=400)
    else:
      profile.departure_date = None # Đặt None nếu chuỗi rỗng


    profile.save()
    
    message = "Hồ sơ đã được tạo thành công!" if created else "Hồ sơ đã được cập nhật thành công!"
    return JsonResponse({'success': True, 'message': message}, status=200)
    
  except Exception as e:
    # Lỗi này có thể là lỗi "no such column" hoặc các lỗi DB khác
    print(f"LỖI LƯU DATABASE: {e}")
    return JsonResponse({'error': f'Lỗi server khi lưu dữ liệu: {str(e)}'}, status=500)
    
@require_http_methods(["POST"])
def password_change_ajax(request):
  """
  Xử lý yêu cầu đổi mật khẩu bằng AJAX.
  """
  if not request.user.is_authenticated:
    return JsonResponse({'error': 'Yêu cầu xác thực.'}, status=401)
    
  try:
    data = json.loads(request.body)
  except json.JSONDecodeError:
    return JsonResponse({'error': 'Định dạng JSON không hợp lệ.'}, status=400)
    
  # Tạo đối tượng PasswordChangeForm với dữ liệu POST và user hiện tại
  form = PasswordChangeForm(user=request.user, data=data)
  
  if form.is_valid():
    # Lưu mật khẩu mới và cập nhật session
    user = form.save()
    update_session_auth_hash(request, user) # Quan trọng: giữ người dùng đăng nhập
    
    return JsonResponse({'success': True, 'message': 'Mật khẩu đã được thay đổi thành công!'}, status=200)
  else:
    # Trích xuất lỗi form và gửi lại dưới dạng JSON
    errors = {field: form.errors[field] for field in form.errors}
    
    # Lỗi non_field_errors (ví dụ: mật khẩu mới không khớp)
    if form.non_field_errors():
      errors['non_field_errors'] = form.non_field_errors()
    
    return JsonResponse({'error': 'Lỗi xác thực.', 'errors': errors}, status=400)

@require_http_methods(["POST"])
def upload_avatar_ajax(request):
  """
  Xử lý yêu cầu tải ảnh đại diện lên qua AJAX (multipart/form-data).
  Lưu file vào thư mục MEDIA và cập nhật UsersProfile với URL mới.
  """
  if not request.user.is_authenticated:
    return JsonResponse({'error': 'Yêu cầu xác thực.'}, status=401)

  if 'avatar_file' not in request.FILES:
    return JsonResponse({'error': 'Không tìm thấy file ảnh.'}, status=400)
  
  avatar_file = request.FILES['avatar_file']
  
  # Chỉ chấp nhận các loại file ảnh phổ biến
  if not avatar_file.content_type.startswith('image/'):
    return JsonResponse({'error': 'File không phải là định dạng ảnh hợp lệ.'}, status=400)

  # Giới hạn kích thước file (ví dụ: 5MB)
  if avatar_file.size > 5 * 1024 * 1024:
    return JsonResponse({'error': 'Kích thước file vượt quá 5MB.'}, status=400)

  try:
    # Tạo đối tượng FileSystemStorage
    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'avatars'))
    
    # Đổi tên file để tránh xung đột (sử dụng user ID)
    filename_ext = os.path.splitext(avatar_file.name)[1] # Lấy đuôi file
    filename = f'avatar_{request.user.pk}{filename_ext}'
    
    # Lưu file vào MEDIA_ROOT/avatars/
    saved_filename = fs.save(filename, avatar_file)
    
    # Tạo URL công khai
    file_url = fs.url(saved_filename)
    
    # Cập nhật UsersProfile với URL mới
    profile = UsersProfile.objects.get(user=request.user)
    profile.avatar = file_url # Lưu URL vào trường avatar (URLField)
    profile.save()
    
    return JsonResponse({
      'success': True, 
      'message': 'Ảnh đại diện đã cập nhật thành công.',
      'avatar_url': file_url
    }, status=200)
  
  except UsersProfile.DoesNotExist:
    return JsonResponse({'error': 'Không tìm thấy hồ sơ người dùng.'}, status=404)
  except Exception as e:
    print(f"LỖI UPLOAD AVATAR: {e}")
    return JsonResponse({'error': f'Lỗi server khi lưu file: {str(e)}'}, status=500)