from django.contrib import admin
from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "address", "created_at")
	prepopulated_fields = {"slug": ("name",)}
	search_fields = ("name", "address")
	readonly_fields = ("created_at", "updated_at")
