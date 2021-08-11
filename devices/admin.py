from django.contrib import admin

# Register your models here.
from .models import Device, Workspace

admin.site.register(Device)
admin.site.register(Workspace)
