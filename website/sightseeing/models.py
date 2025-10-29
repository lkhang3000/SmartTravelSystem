from django.db import models
from django.contrib.auth.models import User

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
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='destinations')
    location = models.CharField(max_length=200, null=True)
    description = models.TextField(max_length=200, null=True)
    price_range = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.desName


