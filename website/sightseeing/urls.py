"""
URL patterns for sightseeing app
"""
from django.urls import path
from . import views

urlpatterns = [
    path("change-email/", views.change_email, name="change_email"),
    # Authentication URLs
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    # Password reset URLs
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
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
]
