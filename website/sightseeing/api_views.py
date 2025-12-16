from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from .models import TripItem, Destinations

@login_required
@require_http_methods(["POST"])
def save_itinerary_item(request):
    """Save or update an itinerary item"""
    try:
        data = json.loads(request.body)
        destination_id = data.get('destination_id')
        day = data.get('day')
        order = data.get('order', 0)
        notes = data.get('notes', '')
        
        if not destination_id or not day:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Get or create destination
        try:
            destination = Destinations.objects.get(id=destination_id)
        except Destinations.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Destination not found'}, status=404)
        
        # Create or update trip item
        trip_item, created = TripItem.objects.update_or_create(
            user=request.user,
            destination=destination,
            defaults={
                'day': day,
                'order': order,
                'notes': notes
            }
        )
        
        return JsonResponse({
            'success': True,
            'item_id': trip_item.id,
            'created': created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_itinerary_note(request):
    """Update note for an itinerary item"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        notes = data.get('notes', '')
        
        if not item_id:
            return JsonResponse({'success': False, 'error': 'Missing item_id'}, status=400)
        
        try:
            trip_item = TripItem.objects.get(id=item_id, user=request.user)
            trip_item.notes = notes
            trip_item.save()
            
            return JsonResponse({'success': True})
        except TripItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_itinerary_item(request):
    """Update an itinerary item (day, order, notes)"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        day = data.get('day')
        order = data.get('order', 0)
        notes = data.get('notes', '')
        
        if not item_id:
            return JsonResponse({'success': False, 'error': 'Missing item_id'}, status=400)
        
        try:
            trip_item = TripItem.objects.get(id=item_id, user=request.user)
            if day is not None:
                trip_item.day = day
            trip_item.order = order
            trip_item.notes = notes
            trip_item.save()
            
            return JsonResponse({'success': True})
        except TripItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_itinerary_item(request):
    """Remove an item from itinerary"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({'success': False, 'error': 'Missing item_id'}, status=400)
        
        try:
            trip_item = TripItem.objects.get(id=item_id, user=request.user)
            trip_item.delete()
            
            return JsonResponse({'success': True})
        except TripItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_all_itinerary(request):
    """Save all itinerary items at once"""
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({'success': False, 'error': 'No items provided'}, status=400)
        
        updated_count = 0
        errors = []
        
        for item_data in items:
            item_id = item_data.get('item_id')
            day = item_data.get('day')
            order = item_data.get('order', 0)
            notes = item_data.get('notes', '')
            
            if not item_id:
                errors.append(f'Missing item_id for item')
                continue
            
            try:
                trip_item = TripItem.objects.get(id=item_id, user=request.user)
                trip_item.day = day
                trip_item.order = order
                trip_item.notes = notes
                trip_item.save()
                updated_count += 1
            except TripItem.DoesNotExist:
                errors.append(f'Item {item_id} not found')
            except Exception as e:
                errors.append(f'Error updating item {item_id}: {str(e)}')
        
        if errors:
            return JsonResponse({
                'success': False if updated_count == 0 else True,
                'updated': updated_count,
                'errors': errors
            })
        
        return JsonResponse({
            'success': True,
            'updated': updated_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_itinerary(request):
    """Get all itinerary items for current user"""
    try:
        trip_items = TripItem.objects.filter(
            user=request.user,
            destination__isnull=False
        ).select_related('destination').order_by('day', 'order')
        
        items_data = []
        for item in trip_items:
            items_data.append({
                'id': item.id,
                'day': item.day,
                'order': item.order,
                'notes': item.notes or '',
                'destination': {
                    'id': item.destination.id,
                    'name': item.destination.desName,
                    'category': item.destination.category or '',
                    'rating': str(item.destination.rating) if item.destination.rating else '',
                    'image': item.destination.image_url or 'https://picsum.photos/400/200',
                    'address': item.destination.address or ''
                }
            })
        
        return JsonResponse({'success': True, 'items': items_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
