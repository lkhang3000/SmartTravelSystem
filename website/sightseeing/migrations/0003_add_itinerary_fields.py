# Generated migration for itinerary functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sightseeing', '0002_alter_trip_price_per_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='tripitem',
            name='order',
            field=models.IntegerField(default=0, help_text='Order of item within the day'),
        ),
        migrations.AddField(
            model_name='tripitem',
            name='notes',
            field=models.TextField(blank=True, null=True, help_text='User notes for this destination'),
        ),
        migrations.AlterField(
            model_name='tripitem',
            name='day',
            field=models.IntegerField(null=True, blank=True, help_text='Day number in the trip (1, 2, 3, etc.)'),
        ),
    ]
