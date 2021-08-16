from random import choices

from django.db import models

from django.utils.translation import gettext_lazy as _

# Create your models here.
from django.db.models.fields import related
from sqlalchemy.orm import properties


class Workspace(models.Model):
    name = models.CharField(max_length=20)

    # devices = models.ManyToManyField(Device, blank=True)

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

    name = models.CharField(max_length=80)
    device_host_id = models.CharField(max_length=120)
    type = models.CharField(max_length=6, choices=DEVICE_TYPE)
    firmware = models.CharField(max_length=20, choices=FIRMWARE, default='tasmota')
    gpio = models.IntegerField(blank=True, null=True)
    sensor_type = models.CharField(max_length=10, blank=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    readings = models.JSONField(blank=True, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['type']


class EventHubMsg(models.Model):
    data = models.JSONField(blank=True, null=True)
    properties = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.pk
