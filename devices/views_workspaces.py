from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, mixins, generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from devices.models import Device, Workspace
from devices.serializers import PkNameSerializer


def attach_device_list_to_workspace(devices, workspace):
    try:
        attached_devices = Device.objects.filter(workspace=workspace)
        # clear previously attached devices
        for device in attached_devices:
            device.workspace = None
            device.save()
        if not devices:
            return
        for device_id in devices:
            device = Device.objects.get(pk=device_id)
            device.workspace = workspace
            device.save()
    except ValueError:
        return {
            'error': 'The device ID isn\'t numeric'
        }
    except ObjectDoesNotExist:
        return {
            'error': 'The device doesn\'t exist'
        }
    except Exception as error:
        return {
            'error': str(error)
        }


class WorkspaceList(APIView):
    def get(self, request):
        workspaces = Workspace.objects.all()
        serializer = PkNameSerializer(workspaces, many=True)
        return Response(serializer.data)

    def post(self, request):
        # add new workspace
        serializer = PkNameSerializer(data=request.data)
        if serializer.is_valid():
            workspace = serializer.save()
            try:
                # attach created workspace to devices
                devices = request.data.get('devices')
                attach_to_devices = attach_device_list_to_workspace(devices, workspace)
                if attach_to_devices:
                    return Response(attach_to_devices, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceDetail(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    queryset = Workspace.objects.all()
    serializer_class = PkNameSerializer

    def get(self, request, *args, **kwargs):
        # @TODO replace this method with new class add devices belongs to the workspace as well
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class WorkspaceSingle(APIView):
    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        w_serializer = PkNameSerializer(workspace)
        devices = Device.objects.filter(workspace__pk=workspace.pk)

        # for devices used the same serializer only two same fields wanted.
        d_serializer = PkNameSerializer(devices, many=True)

        return Response({
            **w_serializer.data,
            'devices': d_serializer.data
        })

    def put(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        serializer = PkNameSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(workspace, serializer.data)
            try:
                # attach created workspace to devices
                devices = request.data.get('devices')
                attach_to_devices = attach_device_list_to_workspace(devices, workspace)
                if attach_to_devices:
                    return Response(attach_to_devices, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                pass
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)