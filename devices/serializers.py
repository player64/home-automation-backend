from rest_framework import serializers

from devices.models import Device, Workspace


class WorkspaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Workspace
        fields = ['pk', 'name']


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    # workspace = WorkspaceSerializer()

    class Meta:
        model = Device
        fields = ['pk', 'name', 'type', 'updated_at', 'readings']
