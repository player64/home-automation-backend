import binascii
import json
from datetime import datetime

from django.shortcuts import render
from rest_framework.exceptions import ValidationError, ParseError, MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets, mixins, generics, status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
import base64

from devices.device_types.device_type_factories import RelayFactory, identify_by_payload
from devices.device_types.exceptions import FirmwareFactoryException, DeviceExceptions

from devices.models import Device, Workspace, EventHubMsg
from devices.serializers import DeviceSerializer, WorkspaceSerializer
from django.utils import timezone
from collections.abc import Iterable


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        workspace_id = request.query_params.get('workspace')
        if workspace_id:
            try:
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
    permission_classes = (IsAuthenticated,)

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
    permission_classes = (IsAuthenticated,)

    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class DeviceList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        snippets = Device.objects.all()
        serializer = DeviceSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetail(mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    queryset = Device.objects.all()
    serializer_class = WorkspaceSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        # print(request.data.get('sensor_type'))
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateReadings(APIView):
    def post(self, request):
        if not isinstance(request.data, list):
            raise MethodNotAllowed(method=self, detail='Request data must be a list')
        for item in request.data:
            try:
                body = item['data']['body']
                properties = item['data']['properties']
                body_decoded = self.__decode_body_msg(body)
                firmware = identify_by_payload(properties)
                firmware_factory = firmware(properties, body_decoded)
                identify = firmware_factory.identify_properties()
                device_factory_instance = identify['factory']
                host_id = identify['device_id']
            except KeyError:
                raise ParseError({'error': 'KeyError. Happened during assigning values body and properties'})
            except NotImplementedError as e:
                # raised by identify_by_payload when firmware not found
                raise MethodNotAllowed(method=self, detail=str(e))
            except json.decoder.JSONDecodeError:
                raise MethodNotAllowed(method=self, detail='Error when trying to convert body to json')
            except binascii.Error:
                raise MethodNotAllowed(method=self, detail='Error when trying to decode body to ascii')
            except FirmwareFactoryException:
                # action not found during identify_properties
                return Response(status=status.HTTP_204_NO_CONTENT)

            devices = Device.objects.filter(device_host_id=host_id)

            for device in devices:
                device_type_factory = device_factory_instance(device).obtain_factory()
                obtained_device = device_type_factory(firmware_factory, device)

                try:
                    device.readings = obtained_device.get_readings()
                    device.updated_at = timezone.now()
                    device.save()
                    print('Device was updated')
                except DeviceExceptions:
                    print('Device wasn\'t updated')
                    continue
            return Response({
                'msg': 'success',
                'data': body_decoded,
            }, status=status.HTTP_201_CREATED)

    @staticmethod
    def __decode_body_msg(body):
        data = base64.b64decode(body)
        msg = data.decode('ascii')
        return json.loads(msg)


class UpdateState(APIView):
    def post(self, request, device_id):
        device = get_object_or_404(Device, pk=device_id)
        if device.type != 'relay':
            raise ValidationError({'error': 'You cannot send the message to sensor type'})

        relay_factory = RelayFactory(device).obtain_factory()
        relay = relay_factory(None, device)

        try:
            relay.message(request.data.get('state'))
        except DeviceExceptions as e:
            Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'result': 'OK'}, status=status.HTTP_200_OK)
