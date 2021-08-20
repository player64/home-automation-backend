from django.contrib import admin

# Register your models here.
from .models import Device, DeviceLog, DeviceEvent, Workspace, EventHubMsg


admin.site.register(Device)
admin.site.register(DeviceLog)
admin.site.register(DeviceEvent)
admin.site.register(Workspace)
admin.site.register(EventHubMsg)
