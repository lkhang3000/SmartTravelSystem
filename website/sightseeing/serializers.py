from rest_framework import serializers

# Note: Place model not present in `models.py`. Import removed.
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'avatar', 'bio']


