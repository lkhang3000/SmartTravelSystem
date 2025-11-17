"""
URL patterns for sightseeing app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    
    # Password reset URLs
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # User pages
    path('profile/', views.user_profile, name='user_profile'),
    path('user-input/', views.user_input, name='user_input'),
    path('save-user-input/', views.save_user_input, name='save_user_input'),
    path('recommend-result/', views.recommend_result, name='recommend_result'),
    
    # Info pages
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
]
