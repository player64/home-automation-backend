from django.contrib import admin

# Register your models here.
from .models import Device, Workspace, EventHubMsg

admin.site.register(Device)
admin.site.register(Workspace)
admin.site.register(EventHubMsg)
