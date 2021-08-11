from rest_framework import serializers

from devices.models import Device


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Device
        fields = ['name', 'type', 'updated_at', 'readings']

