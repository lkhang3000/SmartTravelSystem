from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

#Register form
class registerForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UsersProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=False)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name
    
class Region(models.Model):
    regionName = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.regionName


class Destinations(models.Model):
    desName = models.CharField(max_length=200, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='destinations', null=True, blank=True)
    location = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True, blank=True)
    price_range = models.CharField(max_length=50, null=True, blank=True)
    
    # Thông tin chi tiết
    category = models.CharField(max_length=100, null=True, blank=True)  # Loại hình: Biển, Núi, Di sản...
    rating = models.FloatField(default=0.0, null=True, blank=True)  # Đánh giá 0-5
    address = models.TextField(null=True, blank=True)  # Địa chỉ đầy đủ
    phone = models.CharField(max_length=20, null=True, blank=True)  # Số điện thoại
    website = models.URLField(max_length=500, null=True, blank=True)  # Website
    opening_hours = models.TextField(null=True, blank=True)  # Giờ mở cửa
    image_url = models.URLField(max_length=500, null=True, blank=True)  # Link ảnh đại diện
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.desName
    

