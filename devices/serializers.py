from rest_framework import serializers

from devices.models import Device, Workspace, DeviceLog, DeviceEvent


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['pk', 'name']


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['pk', 'name', 'type', 'updated_at', 'readings', 'sensor_type']


class DeviceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceLog
        fields = ['time', 'readings']


class DeviceDetailSerializer(serializers.ModelSerializer):
    # if class extends serializers.HyperlinkedModelSerializer
    # example below lets add the whole related object in the response rather than pk
    # workspace = WorkspaceSerializer()

    class Meta:
        model = Device
        fields = ['name', 'type', 'firmware', 'gpio', 'sensor_type', 'updated_at', 'readings', 'workspace']


class DeviceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceEvent
        fields = '__all__'
        # read_only_fields = ('device',)


class DeviceReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['readings', 'updated_at']
