from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Place
from .serializers import PlaceSerializer, RecommendationRequestSerializer
from .Services.recommender import recommend


class PlaceViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and retrieving places."""
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [permissions.AllowAny] #Cho phép tất cả truy xuất

#API endpoint
class RecommendationAPIView(APIView):
    """Simple recommendation endpoint. POST validated JSON and return results.

    This is a thin wrapper: it validates the request body with
    `RecommendationRequestSerializer`, calls the pure `recommend` service and
    returns the result list as JSON. The `recommend` function should be
    implemented in `sightseeing/services/recommender.py`.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RecommendationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        results = recommend(validated)
        return Response({"results": results}, status=status.HTTP_200_OK)
