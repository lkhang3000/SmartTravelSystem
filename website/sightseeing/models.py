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
    locationName = models.CharField(max_length=200, null=True)  # Ha Noi, Ho Chi Minh, Da Nang, etc.

    def __str__(self):
        return self.locationName


class Destinations(models.Model):
    # Core fields matching CSV structure
    desName = models.CharField(max_length=200, null=True)  # 'name' in CSV
    address = models.TextField(null=True, blank=True)  # 'address' in CSV
    rating = models.FloatField(default=0.0, null=True, blank=True)  # 'ratings' in CSV
    category = models.CharField(max_length=100, null=True, blank=True)  # 'category' in CSV
    description = models.TextField(null=True, blank=True)  # 'description' in CSV
    
    # Location as ForeignKey (references 'location' in CSV)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='destinations', null=True, blank=True)
    
    # Additional fields not in CSV
    price_range = models.CharField(max_length=50, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.desName
    

