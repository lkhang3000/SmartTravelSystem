from django.db import models


class Place(models.Model):
	"""A simple model representing a sightseeing place."""
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True)
	description = models.TextField(blank=True)
	address = models.CharField(max_length=300, blank=True)
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		verbose_name = "Place"
		verbose_name_plural = "Places"

	def __str__(self):
		return self.name
