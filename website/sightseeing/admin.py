from django.contrib import admin
from django.http import HttpResponse
from .models import *

admin.site.register(UsersProfile)
admin.site.register(Destinations)
admin.site.register(Region)
