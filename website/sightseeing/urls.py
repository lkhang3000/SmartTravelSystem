from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('', views.get_home, name='home'),
    path('discover/', views.user_input, name='user_input'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.signup_page, name='signup_page'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset-done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    path('recommend/', views.recommend_result, name='recommend_result'),
]
