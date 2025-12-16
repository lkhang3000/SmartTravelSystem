from sightseeing.models import TripItem

items = TripItem.objects.all()
print(f'Total items: {items.count()}')
print()

for item in items[:10]:
    print(f'Item {item.id}:')
    print(f'  - day: {item.day}')
    print(f'  - order: {item.order}')
    print(f'  - notes: {item.notes}')
    if item.destination:
        print(f'  - destination: {item.destination.desName}')
    print()
