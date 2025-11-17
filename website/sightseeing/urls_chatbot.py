"""
URL patterns cho chatbot
"""
from django.urls import path
from . import views_chatbot

urlpatterns = [
    # API endpoint cho chatbot
    path('api/chat/', views_chatbot.chat_with_gemini, name='chat_gemini'),
]
