from django.core.management.base import BaseCommand
from sightseeing.Services.search_history_utils import generate_search_history_csv

class Command(BaseCommand):
    help = 'Generate search history CSV file for recommender system'

    def handle(self, *args, **options):
        self.stdout.write('Generating search history CSV...')
        csv_path = generate_search_history_csv()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated search history CSV at: {csv_path}')
        )