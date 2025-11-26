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
    custom_user_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Custom ID like user_001
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
    destination_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Custom ID like dest_001
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

    def __str__(self):
        return self.desName

class Hotel(models.Model):
    name = models.CharField(max_length=200, null=True)
    hotel_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Custom ID like hotel_001
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='hotels', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    rating = models.FloatField(default=0.0, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)  # Giá phòng, có thể là VND
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

class SearchHistory(models.Model):
    user_id = models.CharField(max_length=20)  # Custom user ID like user_001
    destination_id = models.CharField(max_length=20)  # Custom destination ID like dest_001
    score = models.FloatField()  # User preference score based on actions (0-5 scale)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user_id} - {self.destination_id} - {self.score}"

class TripItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'destination']

    def __str__(self):
        return f"{self.user.username} - {self.destination.desName}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.destination.desName} - {self.content[:50]}"

