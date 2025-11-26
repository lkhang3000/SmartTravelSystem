from sightseeing.models import TripItem

def trip_count(request):
    """Context processor to add trip count to all templates"""
    if request.user.is_authenticated:
        count = TripItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'trip_count': count}