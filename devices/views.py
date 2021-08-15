from datetime import datetime

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets, mixins, generics, status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from devices.models import Device, Workspace, EventHubMsg
from devices.serializers import DeviceSerializer, WorkspaceSerializer


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
        event = EventHubMsg(data=request.data, updated_at=datetime.today())
        event.save()
        return Response({}, status=status.HTTP_201_CREATED)


"""

    def get_object(self, pk):
        try:
            return Workspace.objects.get(pk=pk)
        except Workspace.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = WorkspaceSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = WorkspaceSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
