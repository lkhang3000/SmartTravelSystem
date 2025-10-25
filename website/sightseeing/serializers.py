from rest_framework import serializers
from .models import Place


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "address",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]


class UserLocationSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6)


class RecommendationRequestSerializer(serializers.Serializer):
    preferences = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, allow_empty=True
    )
    budget = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    candidate_slugs = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False, allow_empty=True
    )
    user_location = UserLocationSerializer(required=False)
    max_results = serializers.IntegerField(required=False, default=5, min_value=1, max_value=50)

    def validate(self, data):
        # Optionally enforce custom rules here. For now accept any valid combination.
        return data
