from django.urls import path, include
from rest_framework import routers
from . import views

# `PlaceViewSet` was removed from `sightseeing.api_views`.
# If you re-add API viewsets later, register them on the router here.
router = routers.DefaultRouter()

urlpatterns = [
    # POST endpoint: frontend sends user filter/input here
    path("recommend/", views.api_recommend, name="api_recommend"),
    path("", include(router.urls)),
]
