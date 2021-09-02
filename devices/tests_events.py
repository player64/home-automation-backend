from rest_framework.test import APITestCase
from devices.tests import authenticate
from devices.models import Device, DeviceEvent


class TestDeviceEvents(APITestCase):
    def setUp(self):
        self.client = authenticate(self.client)

    @staticmethod
    def __create_test_device(device_type='relay'):
        return Device.objects.create(name='Test', device_host_id='t1', type=device_type, firmware='tasmota', gpio=1)

    def test_get_event(self):
        device = self.__create_test_device()
        event = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time='18:30')
        response = self.client.get('/api/v1/devices/event/%i/' % event.pk)

        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['name'], 'Event')
        self.assertEqual(content['device'], device.pk)
        self.assertEqual(content['type'], 'time')
        self.assertEqual(content['action'], 'ON')
        self.assertEqual(content['time'], '18:30:00')

    def test_update_event(self):
        device = self.__create_test_device()
        event = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time='18:30')
        response = self.client.put('/api/v1/devices/event/%i/' % event.pk, {
            'name': 'Title updated',
            'action': 'OFF',
            'device': device.pk,
            'time': '17:32'
        })
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['name'], 'Title updated')
        self.assertEqual(content['device'], device.pk)
        self.assertEqual(content['type'], 'time')
        self.assertEqual(content['action'], 'OFF')
        self.assertEqual(content['time'], '17:32:00')

    def test_create_event(self):
        device = self.__create_test_device()
        response = self.client.post('/api/v1/devices/event/', {
            'name': 'Event',
            'device': device.pk,
            'type': 'time',
            'action': 'OFF',
            'time': '17:32'
        })
        content = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(content['name'], 'Event')
        self.assertEqual(content['device'], device.pk)
        self.assertEqual(content['type'], 'time')
        self.assertEqual(content['action'], 'OFF')
        self.assertEqual(content['time'], '17:32:00')

    def test_delete_event(self):
        device = self.__create_test_device()
        event = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time='18:30')
        self.assertEqual(len(DeviceEvent.objects.all()), 1)
        response = self.client.delete('/api/v1/devices/event/%i/' % event.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(DeviceEvent.objects.all()), 0)
