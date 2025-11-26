"""
URL patterns for sightseeing app
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    path('logout/', views.logout_view, name='logout'),
    
    # # Password reset URLs
    # path('password-reset/', views.password_reset, name='password_reset'),
    # path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    # path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    # path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # --- URL Đổi Mật Khẩu (Tích hợp AJAX) ---
    path('password-change/ajax/', views.password_change_ajax, name='password_change_ajax'), 

    # --- URL Upload Avatar AJAX ---
    path('profile/upload-avatar/', views.upload_avatar_ajax, name='upload_avatar_ajax'), 

    # --- URL Mặc định Đổi Mật Khẩu (Nếu cần) ---
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='password_change_form.html',
        success_url=reverse_lazy('password_change_done') 
    ), name='password_change'),
    
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='password_change_done.html'
    ), name='password_change_done'),
    #Function pages
    path('Trip-planner/', views.trip_planner, name='trip_planner'),

    # User pages
    path('profile/', views.user_profile, name='user_profile'),
    path('user-input/', views.user_input, name='user_input'),
    path('save-user-input/', views.save_user_input, name='save_user_input'),
    path('recommend-result/', views.recommend_result, name='recommend_result'),
    path('destination/<int:destination_id>/', views.destination_detail, name='destination_detail'),
    path('destination/<int:destination_id>/add-trip/', views.add_to_trip, name='add_to_trip'),
    path('trip/', views.trip_list, name='trip_list'),
    path('trip/remove/<int:trip_item_id>/', views.remove_from_trip, name='remove_from_trip'),
    path('destination/', views.user_profile, name='destination'),
    path('profile/edit/', views.edit_profile_data, name='edit_profile'),
    
    
    # Info pages
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
]
