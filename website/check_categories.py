from sightseeing.models import Destinations

categories = Destinations.objects.values_list('category', flat=True).distinct().order_by('category')
categories = [cat for cat in categories if cat]

print('Categories in database:')
for i, cat in enumerate(categories, 1):
    count = Destinations.objects.filter(category=cat).count()
    print(f'{i}. {cat} ({count} destinations)')

print(f'\nTotal categories: {len(categories)}')

print('\nSample destinations:')
sample_dests = Destinations.objects.all()[:5]
for dest in sample_dests:
    print(f'- {dest.desName}: category="{dest.category}"')