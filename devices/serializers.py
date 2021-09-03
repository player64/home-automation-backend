from rest_framework import serializers

from devices.models import Device, Workspace, DeviceLog, DeviceEvent


class PkNameSerializer(serializers.ModelSerializer):
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


class DeviceInfoSerializer(serializers.HyperlinkedModelSerializer):
    # if class extends serializers.HyperlinkedModelSerializer
    # it adds the whole related object in the response rather than pk
    workspace = PkNameSerializer()

    class Meta:
        model = Device
        fields = ['pk', 'name', 'type', 'firmware', 'updated_at', 'device_host_id', 'gpio', 'sensor_type', 'workspace']


class DeviceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['pk', 'name', 'type', 'firmware', 'updated_at', 'device_host_id', 'gpio', 'sensor_type', 'workspace']


class DeviceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceEvent
        fields = '__all__'
        # read_only_fields = ('device',)


class DeviceReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['readings', 'updated_at']
