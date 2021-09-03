from rest_framework import mixins, generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from devices.models import Device, DeviceEvent
from devices.serializers import PkNameSerializer, DeviceEventSerializer


class EventsDeviceList(APIView):
    def get(self, request, device_id):
        """
        Get device's events
        :param request:
        :param device_id:
        :return:
        """
        device = get_object_or_404(Device, pk=device_id)
        events = DeviceEvent.objects.filter(device=device)
        events_serializer = PkNameSerializer(events, many=True)
        return Response(events_serializer.data)


class DeviceEventDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = DeviceEvent.objects.all()
    serializer_class = DeviceEventSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        validate = ValidateEvent()
        validate.is_valid(request)
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ValidateEvent:

    def is_valid(self, request):
        event_types = {
            'time': self.time_fields,
            'sensor': self.sensor_fields,
        }
        event_type = request.data.get('type')
        if not event_type:
            raise ValidationError({'error': 'The event type is required'})
        try:
            fields = event_types[event_type]()
            return self.validate(request, fields)
        except KeyError:
            raise ValidationError({'error': 'This event type isn\'t implemented'})

    def validate(self, request, fields):
        for field in fields:
            if not request.data.get(field['key']):
                raise ValidationError({'error': field['error']})

    def time_fields(self):
        return [{
            'key': 'time',
            'error': 'The time is required'
        }]

    def sensor_fields(self):
        return [
            {
                'key': 'sensor',
                'error': 'Sensor is required'
            },
            {
                'key': 'reading_type',
                'error': 'Sensor reading type is required'
            },
            {
                'key': 'rule',
                'error': 'Rule is required'
            },
            {
                'key': 'value',
                'error': 'Sensor value reading is required'
            },
        ]


class DeviceEventCreate(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = DeviceEvent.objects.all()
    serializer_class = DeviceEventSerializer

    def post(self, request, *args, **kwarg):
        validate = ValidateEvent()
        validate.is_valid(request)

        return self.create(request, *args, **kwarg)
