from django.urls import path, include
from rest_framework import routers

# `PlaceViewSet` was removed from `sightseeing.api_views`.
# If you re-add API viewsets later, register them on the router here.
router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
]
