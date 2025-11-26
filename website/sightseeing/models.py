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
    
class Location(models.Model):
    locationName = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.locationName


class Destinations(models.Model):
    desName = models.CharField(max_length=200, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='destinations', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price_range = models.CharField(max_length=50, null=True, blank=True)
    
    # Thông tin chi tiết
    category = models.CharField(max_length=100, null=True, blank=True)  # Loại hình: Biển, Núi, Di sản...
    rating = models.FloatField(default=0.0, null=True, blank=True)  # Đánh giá 0-5
    address = models.TextField(null=True, blank=True)  # Địa chỉ đầy đủ
    image_url = models.URLField(max_length=500, null=True, blank=True)  # Link ảnh đại diện
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ['desName', 'location']  # Đảm bảo không có destination trùng tên trong cùng location

    def __str__(self):
        return self.desName


# Model Hotel riêng, liên kết với Location và điểm du lịch gần nhất
class Hotel(models.Model):
    name = models.CharField(max_length=200, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='hotels', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    rating = models.FloatField(default=0.0, null=True, blank=True)
    price = models.CharField(max_length=50, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    # Liên kết với điểm du lịch gần nhất (có thể null)
    nearest_destination = models.ForeignKey(Destinations, on_delete=models.SET_NULL, null=True, blank=True, related_name='nearby_hotels')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name
    

