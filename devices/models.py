from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Device(models.Model):
    DEVICE_TYPE = (
        ('sensor', 'Sensor'),
        ('relay', 'Relay'),
    )

    FIRMWARE = (
        ('tasmota', 'Tasmota'),
        ('simulated', 'Simulated')
    )

    SENSOR_TYPE = (
        (None, '---'),
        ('am2301', 'AM2301')
    )

    name = models.CharField(max_length=80)
    device_host_id = models.CharField(max_length=120)
    type = models.CharField(max_length=6, choices=DEVICE_TYPE)
    firmware = models.CharField(max_length=20, choices=FIRMWARE, default='tasmota')
    gpio = models.IntegerField(blank=True, null=True)
    sensor_type = models.CharField(max_length=10, choices=SENSOR_TYPE, default=None, null=True, blank=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    readings = models.JSONField(blank=True, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.SET_NULL, default=None, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['type']


class DeviceLog(models.Model):
    # recent_update.objects.order_by('-created_date')
    time = models.DateTimeField(auto_now_add=True)
    readings = models.JSONField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    def __str__(self):
        return 'Log for %s' % self.device.name

    class Meta:
        ordering = ['-time']


class DeviceEvent(models.Model):
    TYPES = (
        ('time', 'Time'),
        ('sensor', 'Sensor')
    )
    ACTIONS = (
        ('ON', 'ON'),
        ('OFF', 'OFF')
    )
    RULES = (
        ('=', '='),
        ('>', '>'),
        ('>=', '>='),
        ('<=', '<='),
        ('<', '<')
    )

    name = models.CharField(max_length=80)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPES, default='time')
    action = models.CharField(max_length=10, choices=ACTIONS, default='OFF')
    # optional fields for time event type
    time = models.TimeField(null=True, blank=True)

    # optional fields for sensor type
    sensor = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='sensor')
    reading_type = models.CharField(max_length=40, null=True, blank=True)
    rule = models.CharField(max_length=3, choices=RULES, null=True, blank=True)
    value = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class EventHubMsg(models.Model):
    data = models.JSONField(blank=True, null=True)
    properties = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.pk)
