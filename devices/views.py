import json
from datetime import datetime

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets, mixins, generics, status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
import base64
from devices.models import Device, Workspace, EventHubMsg
from devices.serializers import DeviceSerializer, WorkspaceSerializer
from django.utils import timezone
from collections.abc import Iterable
from devices.firmwareFactory import FirmwareIdentifier, TasmotaFactory, AM2302Factory, RelayFactory, SensorFactory


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
        snippets = Workspace.objects.all()
        serializer = WorkspaceSerializer(snippets, many=True)
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
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class EventHub(APIView):
    def post(self, request):
        if isinstance(request.data, list):
            for item in request.data:
                try:
                    body = item['data']['body']
                    properties = item['data']['properties']
                except KeyError:
                    return Response({}, status=status.HTTP_400_BAD_REQUEST)

                body_decoded = self.__decode_body_msg(body)
                #
                firmware_instance = FirmwareIdentifier.identify(properties)

                # obtain firmware factory this is child of FirmwareFactory
                firmware_factory = firmware_instance(properties, body_decoded)

                device_factory_type = firmware_factory.identify()

                try:
                    device_factory_instance = device_factory_type['factory']
                    host_id = device_factory_type['device_id']
                except KeyError:
                    return Response({}, status=status.HTTP_204_NO_CONTENT)

                if not device_factory_instance:
                    return Response({}, status=status.HTTP_204_NO_CONTENT)

                devices = Device.objects.filter(device_host_id=host_id)

                for device in devices:
                    factory_device_type = device_factory_instance(device)  # RelayFactory(device) init
                    type_factory = factory_device_type.obtain()
                    obtained_device = type_factory(firmware_factory, device)

                    device.readings = obtained_device.get_readings()
                    device.updated_at = timezone.now()
                    device.save()

                return Response({
                    'msg': 'success',
                    'data': body_decoded,
                }, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @staticmethod
    def __decode_body_msg(body):
        data = base64.b64decode(body)
        msg = data.decode('ascii')
        return json.loads(msg)
