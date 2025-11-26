"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from sightseeing import views
from django.conf import settings
from django.conf.urls.static import static

# ... (các urlpatterns hiện tại)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.get_home, name='home'),
    
    # Chatbot Gemini
    path('', include('sightseeing.urls_chatbot')),
    path("chat/api/", include("chatservice.urls")),

    # Include sightseeing app URLs (without api/ prefix for user-facing pages)
    path('', include('sightseeing.urls')),
    path('account/', include('account.urls')),
    path('chat/', include('chatservice.urls')),
]

# Đây là nơi BẮT BUỘC để đặt code phục vụ MEDIA files:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
