import binascii
from datetime import datetime
import json
from urllib.request import Request

from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import mixins, generics, status
from rest_framework.views import APIView
import base64

from devices.device_types.device_type_factories import RelayFactory, identify_by_payload
from devices.device_types.exceptions import FirmwareFactoryException, DeviceException

from devices.models import Device, Workspace, DeviceLog, DeviceEvent
from devices.serializers import DeviceSerializer, WorkspaceSerializer, DeviceDetailSerializer, DeviceLogSerializer, \
    DeviceEventSerializer, DeviceReadingSerializer
from django.utils import timezone
import logging

logger = logging.getLogger('django')


class DashboardView(APIView):
    def get(self, request):
        workspace_id = request.query_params.get('workspace')
        if workspace_id:
            try:
                # TODO: change this to get_object_or_404
                workspace = Workspace.objects.get(pk=workspace_id)
            except ValueError:
                # get unassigned devices
                workspace = False

        else:
            workspace = Workspace.objects.order_by('name').first()

        if workspace:
            relays = Device.objects.filter(workspace__pk=workspace.pk).filter(type='relay')
            sensors = Device.objects.filter(workspace__pk=workspace.pk).filter(type='sensor')
        else:
            relays = Device.objects.filter(type='relay')
            sensors = Device.objects.filter(type='sensor')

        workspaces = Workspace.objects.all()
        w_serializer = WorkspaceSerializer(workspaces, many=True)
        r_serializer = DeviceSerializer(relays, many=True)
        s_serializer = DeviceSerializer(sensors, many=True)
        content = {
            'devices': {
                'relays': r_serializer.data,
                'sensors': s_serializer.data
            },
            'workspaces': w_serializer.data
        }
        return Response(content)


class WorkspaceList(APIView):
    def get(self, request):
        workspaces = Workspace.objects.all()
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceDetail(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get(self, request, *args, **kwargs):
        # @TODO replace this method with new class add devices belongs to the workspace as well
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class WorkspaceSingleWithDevices(APIView):
    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        w_serializer = WorkspaceSerializer(workspace)
        devices = Device.objects.filter(workspace__pk=workspace.pk)

        # for devices used the same serializer only two same fields wanted.
        d_serializer = WorkspaceSerializer(devices, many=True)

        return Response({
            **w_serializer.data,
            'devices': d_serializer.data
        })


class DeviceSearch(APIView):
    def get(self, request):
        search_by = request.query_params.get('name')
        if len(search_by) < 2:
            raise ValidationError('You must enter at least 2 character to search.')

        devices = Device.objects.filter(name__contains=search_by)
        # for devices used the same serializer only two same fields wanted.
        d_serializer = WorkspaceSerializer(devices, many=True)
        return Response(d_serializer.data)


class DeviceEventDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = DeviceEvent.objects.all()
    serializer_class = DeviceEventSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        # @TODO: add validation if sensor
        return self.update(request, *args, **kwargs)


class DeviceEventCreate(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = DeviceEvent.objects.all()
    serializer_class = DeviceEventSerializer

    def post(self, request, *args, **kwarg):
        event_type = request.data.get('type')
        time = request.data.get('time')
        sensor = request.data.get('time')
        reading_type = request.data.get('reading_type')
        rule = request.data.get('rule')
        value = request.data.get('value')

        if event_type == 'time' and not time:
            raise ValidationError({'error': 'Time cannot be empty'})

        return self.create(request, *args, **kwarg)


class DeviceList(APIView):

    def get(self, request):
        """
        Get all devices
        :param request:
        :return: Response
        """
        devices = Device.objects.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Add new device
        :param request:
        :return: Response
        """
        serializer = DeviceSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceSingle(APIView):
    def get(self, request, device_id):
        """
        Get single device with related Logs and Events
        :param device_id:
        :param request:
        :return: Response
        """
        device = get_object_or_404(Device, pk=device_id)
        d_serializer = DeviceDetailSerializer(device)
        # filter logs to today
        _today = datetime.today().strftime('%Y-%m-%d')
        logs = DeviceLog.objects.filter(device=device, time__contains=str(_today))

        l_serializer = DeviceLogSerializer(logs, many=True)
        workspaces = Workspace.objects.all()
        w_serializer = WorkspaceSerializer(workspaces, many=True)

        content = {
            **d_serializer.data,
            'logs': l_serializer.data,
            'workspaces': w_serializer.data,
        }

        if device.type == 'relay':
            # for relay only events are available
            events = DeviceEvent.objects.filter(device=device)
            e_serializer = DeviceEventSerializer(events, many=True)
            # add sensor list that would be used on the event tab
            sensors = Device.objects.filter(type='sensor')
            # needed only pk and name workspace serializer is sufficient
            sensors_serializer = WorkspaceSerializer(sensors, many=True)

            content.update({
                'events': e_serializer.data,
                'sensors': sensors_serializer.data
            })

        return Response(content)


class DeviceDetail(mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   generics.GenericAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceDetailSerializer

    def get(self, request, *args, **kwargs):
        # @TODO: to remove
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        # print(request.data.get('sensor_type'))
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class DeviceReadings(APIView):
    def get(self, request, device_id):
        """
        Method for getting a device readings
        :return: Response
        """
        device = get_object_or_404(Device, pk=device_id)
        serializer = DeviceReadingSerializer(device)
        return Response(serializer.data)


class UpdateReadings(APIView):
    @staticmethod
    def __decode_body_msg(body) -> dict:
        """
        Method to decode a body payload from Azure IoT Hub and return as JSON
        :param body:
        :return: json
        """
        data = base64.b64decode(body)
        msg = data.decode('ascii')
        return json.loads(msg)

    def post(self, request: Request):
        """
        Mathod used for update devices readings
        :param request: Request
        :return: Response
        """
        if not isinstance(request.data, list):
            logger.error('UpdateReadings - Supplied %s needed list' % str(type(request.data)))
            raise MethodNotAllowed(method=self, detail='Request data must be a list')
        for item in request.data:
            try:
                body = item['data']['body']
                properties = item['data']['properties']
                body_decoded = self.__decode_body_msg(body)
                firmware = identify_by_payload(properties)
                firmware_factory = firmware(properties, body_decoded)
                identify = firmware_factory.identify_payload()
                device_factory_instance = identify['factory']
                host_id = identify['device_id']
                save_to_db = identify['save_to_db']
            except KeyError:
                logger.error('UpdateReadings - KeyError. Happened during assigning values body and properties')
                continue
            except NotImplementedError as e:
                logger.error('UpdateReadings - %s' % str(e))
                continue
            except json.decoder.JSONDecodeError:
                logger.error('UpdateReadings - Error when trying to convert body to json')
                continue
            except binascii.Error:
                logger.error('UpdateReadings - Error when trying to decode body to ascii')
                continue
            except FirmwareFactoryException:
                logger.warning('UpdateReadings - Action not found during identify_properties')
                continue

            devices = Device.objects.filter(device_host_id=host_id)

            for device in devices:
                try:
                    device_type_factory = device_factory_instance(device).obtain_factory()
                    obtained_device = device_type_factory(firmware_factory, device)
                    readings = obtained_device.get_readings()
                    device.readings = readings
                    device.updated_at = timezone.now()
                    device.save()
                    # save this event to the database
                    if save_to_db:
                        DeviceLog.objects.create(readings=readings, device=device)

                except DeviceException as e:
                    logger.warning(
                        'UpdateReadings - Readings were not updated; %s; Device - %s' % (str(e), device.name))
                    continue
        return Response({
            'msg': 'success',
        }, status=status.HTTP_201_CREATED)


class UpdateState(APIView):
    def post(self, request, device_id):
        device = get_object_or_404(Device, pk=device_id)
        if device.type != 'relay':
            raise ValidationError({'error': 'You cannot send the message to sensor type'})
        try:
            relay_factory = RelayFactory(device).obtain_factory()
            relay = relay_factory(None, device)
            result = relay.message(request.data.get('state'))
            return Response(result, status=status.HTTP_200_OK)
        except DeviceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# add to the report
class DeviceLogByDate(APIView):
    def get(self, request, device_id):
        device = get_object_or_404(Device, pk=device_id)
        _date = request.query_params.get('date')
        if not _date:
            _date = datetime.today().strftime('%Y-%m-%d')
        try:
            converted_date = datetime.strptime(_date, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'The date format must be as follows Y-m-d'}, status=status.HTTP_400_BAD_REQUEST)

        logs = DeviceLog.objects.filter(device=device, time__year=converted_date.year, time__month=converted_date.month,
                                        time__day=converted_date.day)
        serialized_data = DeviceLogSerializer(logs, many=True)
        return Response(serialized_data.data)
