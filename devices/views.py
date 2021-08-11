from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from devices.models import Device
from devices.serializers import DeviceSerializer


class DashboardView(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('type')
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)