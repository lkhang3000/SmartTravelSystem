"""
URL patterns for sightseeing app
"""
from django.urls import path
from . import views
from . import api_views
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import CustomPasswordResetConfirmView
from django.views.generic import TemplateView
from django.contrib.auth.views import PasswordResetView
from . import views
from . import views_chatbot

urlpatterns = [
    path(
        'password-reset/',
        PasswordResetView.as_view(
            template_name='password_reset.html'
        ),
        name='password_reset'
    ),
    path("change-email/", views.change_email, name="change_email"),
    # Authentication URLs
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    # Password reset URLs
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
     path(
        'reset/<uidb64>/<token>/',
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    
    path(
    'reset/complete/',
    TemplateView.as_view(template_name='password_reset_complete.html'),
    name='password_reset_complete'
),
    
    # Itinerary API URLs
    path('api/itinerary/save/', api_views.save_itinerary_item, name='api_save_itinerary'),
    path('api/itinerary/update/', api_views.update_itinerary_item, name='api_update_itinerary'),
    path('api/itinerary/update-note/', api_views.update_itinerary_note, name='api_update_note'),
    path('api/itinerary/remove/', api_views.remove_itinerary_item, name='api_remove_itinerary'),
    path('api/itinerary/get/', api_views.get_itinerary, name='api_get_itinerary'),
    
    #Function pages
    path('Trip-planner/', views.trip_planner, name='trip_planner'),
    path('input-trip-planner/', views.input_trip_planner, name='input_trip_planner'),
    path('trip-form/', views.trip_form, name='trip_form'),
    path('update-trip-settings/', views.update_trip_settings, name='update_trip_settings'),
    
    # Trip Planner specific URLs (AJAX for Trip Planner page)
    path('destination/<int:destination_id>/add-trip/', views.add_to_trip, name='add_to_trip'),
    
    # Other pages URLs (with messages and redirect)
    path('add-to-trip/<int:destination_id>/', views.add_destination_to_trip, name='add_destination_to_trip'),
    
    path('auto-fill-day/', views.auto_fill_day, name='auto_fill_day'),
    path('optimize-route/', views.optimize_route, name='optimize_route'),

    # User pages
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/delete-trip/<int:trip_id>/', views.delete_trip, name='delete_trip'),
    path('profile/clear-history/', views.clear_history, name='clear_history'),
    path('user-input/', views.user_input, name='user_input'),
    path('save-user-input/', views.save_user_input, name='save_user_input'),
    path('recommend-result/', views.recommend_result, name='recommend_result'),
    path('destination/<int:destination_id>/', views.destination_detail, name='destination_detail'),
    path('destination/<int:destination_id>/add-trip/', views.add_to_trip, name='add_to_trip'),
    path('hotel/<int:hotel_id>/add-trip/', views.add_hotel_to_trip, name='add_hotel_to_trip'),
    path('trip/', views.trip_list, name='trip_list'),
    path('trip/remove/<int:trip_item_id>/', views.remove_from_trip, name='remove_from_trip'),
    path('trip/save-day-selections/', views.save_day_selections, name='save_day_selections'),
    path('destination/', views.user_profile, name='destination'),
    
    # Info pages
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),

    path("update-trip/", views.update_trip, name="update_trip"),
    path('api/save-full-trip/', views.save_trip_api, name='save_trip_api'),
    path('update-profile-settings/', views.update_profile_settings, name='update_profile_settings'),
    path('api/chat/', views_chatbot.chat_with_gemini, name='api_chat'),
]
