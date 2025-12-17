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
    category = models.CharField(max_length=100, null=True, blank=True)  # Loại hình: Shopping Mall, Entertainment, Museum, etc.
    rating = models.FloatField(default=0.0, null=True, blank=True)  # Đánh giá 0-5
    address = models.TextField(null=True, blank=True)  # Địa chỉ đầy đủ
    image_url = models.URLField(max_length=500, null=True, blank=True)  # Link ảnh đại diện (deprecated - use image_urls)
    image_urls = models.TextField(null=True, blank=True)  # Multiple image URLs separated by " ||| "
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


    def get_image_list(self):
        """Return list of image URLs"""
        if self.image_urls:
            return [url.strip() for url in self.image_urls.split('|||') if url.strip()]
        elif self.image_url:
            return [self.image_url]
        return []

    def get_thumbnail_url(self):
        """
        Return the thumbnail URL (second image if available, otherwise first).
        HTTP checking is handled by template onerror fallback.
        """
        images = self.get_image_list()
        if len(images) > 1:
            # Skip the first image, use the second one (usually better quality)
            return images[1]
        elif len(images) == 1:
            return images[0]
        else:
            return None

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

class Restaurant(models.Model):
    name = models.CharField(max_length=200, null=True)
    restaurant_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Custom ID like rest_001
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='restaurants', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    rating = models.FloatField(default=0.0, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)  # Giá trung bình một người, VND
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

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200, null=True, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    budget = models.IntegerField(null=True, blank=True)  # Budget in million VND
    travelers = models.IntegerField(default=1, null=True, blank=True)
    price_per_person = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )  # Price per person in VND
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.destination}"

class TripItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True, help_text='Day number in the trip (1, 2, 3, etc.)')
    order = models.IntegerField(default=0, help_text='Order of item within the day')
    notes = models.TextField(blank=True, null=True, help_text='User notes for this destination')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'destination', 'hotel']
        ordering = ['day', 'order']

    def __str__(self):
        if self.destination:
            return f"{self.user.username} - Day {self.day} - {self.destination.desName}"
        elif self.hotel:
            return f"{self.user.username} - Day {self.day} - {self.hotel.name}"
        return f"{self.user.username} - Unknown"

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


class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, related_name='user_ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'destination')  # One rating per user per destination
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.destination.desName} - {self.rating} stars"

