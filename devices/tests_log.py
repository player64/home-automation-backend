import json
from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework.test import APITestCase

from devices.models import Device, DeviceLog
from devices.tests import authenticate


class TestDeviceLogs(APITestCase):
    def setUp(self):
        self.client = authenticate(self.client)

    def test_get_device_logs(self):
        # create two devices
        dev1 = Device.objects.create(name='Relay 1', type='relay', device_host_id='t1')
        dev2 = Device.objects.create(name='Relay 2', type='relay', device_host_id='t1')

        # create 10 logs for devices for today
        for i in range(1, 10):
            _now = datetime.today().strftime('%Y-%m-%d')
            _date = datetime.strptime(str(_now), '%Y-%m-%d')
            _now = _date.replace(hour=i)

            DeviceLog.objects.create(device=dev1, readings={'state': 'OFF'})
            DeviceLog.objects.create(device=dev2, readings={'state': 'OFF'})

        # add some other dates
        for i in range(1, 30):
            _date = '2021-05-%d' % i
            log1 = DeviceLog.objects.create(device=dev1, readings={'state': 'OFF'})
            # rewrite date
            log1.time = make_aware(datetime.strptime(_date, '%Y-%m-%d'))
            log1.save()

            log2 = DeviceLog.objects.create(device=dev2, readings={'state': 'OFF'})
            log2.time = make_aware(datetime.strptime(_date, '%Y-%m-%d'))
            log2.save()

        response = self.client.get('/api/v1/devices/log/%i/' % dev1.pk)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_json), 9)

        # check with custom date
        response = self.client.get('/api/v1/devices/log/%i/?date=2021-05-23' % dev2.pk)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_json), 1)

    def test_response_with_incorrect_date(self):
        dev1 = Device.objects.create(name='Relay 1', type='relay', device_host_id='t1')
        response = self.client.get('/api/v1/devices/log/%i/?date=pretending_date' % dev1.pk)
        self.assertEqual(response.status_code, 400)

    def test_response_with_incorrect_device(self):
        response = self.client.get('/api/v1/devices/log/1/')
        self.assertEqual(response.status_code, 404)
