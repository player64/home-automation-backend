import base64
import json

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from devices.models import Device, Workspace, DeviceLog, DeviceEvent


def authenticate(client):
    User.objects.create_user(email='email@email.com', username='username', password='password')
    response = client.post('/api/v1/users/login/', {
        'username': 'username',
        'password': 'password'
    }, follow=True)
    token = response.json()
    client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token['access']))
    return client


class TestDevices(APITestCase):
    def setUp(self):
        self.client = authenticate(self.client)

    @staticmethod
    def __convert_dict_to_base64(payload: dict):
        payload_json = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(payload_json).decode()

    def test_get_device(self):
        w = Workspace.objects.create(name='Workspace')
        device = Device(name='Test device', device_host_id='t1', type='relay', firmware='tasmota', gpio=1, workspace=w)
        device.save()
        # add 10 logs and workspaces
        for i in range(1, 11):
            DeviceLog.objects.create(readings={'state': 'on'}, device=device)
            Workspace.objects.create(name='Workspace %d' % i)

        # add one log to check filter is working as expected
        other_dev = Device(name='Test device', device_host_id='t1')
        other_dev.save()
        DeviceLog.objects.create(readings={'state': 'OFF'}, device=other_dev)

        response = self.client.get('/api/v1/devices/single/%i/' % device.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('logs' in content)
        self.assertEqual(len(content['logs']), 10)

        self.assertTrue('workspaces' in content)
        self.assertEqual(len(content['workspaces']), 11)
        self.assertEqual(content['name'], 'Test device')

    def test_get_device_with_events(self):
        device = Device(name='Test device', device_host_id='t1', type='relay')
        device.save()
        # add five events
        for i in range(1, 6):
            event = DeviceEvent(name='Event %d' % i, device=device, type='time', action='ON', time='18:30')
            event.save()
        response = self.client.get('/api/v1/devices/single/%i/' % device.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('events' in content)
        self.assertEqual(len(content['events']), 5)
        self.assertEqual(content['name'], 'Test device')

    def test_get_device_sensor(self):
        # check json structure it shouldn't return events
        device = Device(name='Test device', device_host_id='t1', type='sensor')
        device.save()
        response = self.client.get('/api/v1/devices/single/%i/' % device.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse('events' in content)
        self.assertTrue('workspaces' in content)
        self.assertTrue('logs' in content)

    def test_update_device_with_workspace(self):
        w = Workspace.objects.create(name='Workspace')
        device = Device(name='Test device')
        device.save()
        response = self.client.put('/api/v1/devices/%i/' % device.pk, {
            'name': 'Test',
            'type': 'sensor',
            'workspace': w.pk
        })
        self.assertEqual(response.status_code, 200)
        d = Device.objects.get(pk=1)
        self.assertEqual(d.name, 'Test')
        self.assertEqual(d.workspace.pk, 1)

    def test_update_device_with_empty_name(self):
        device = Device(name='Test device')
        device.save()
        response = self.client.put('/api/v1/devices/%i/' % device.pk)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['name'][0], 'This field is required.')

    def test_delete_device(self):
        device = Device(name='Test device')
        device.save()
        self.assertEqual(Device.objects.all().count(), 1)
        response = self.client.delete('/api/v1/devices/%i/' % device.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Device.objects.all().count(), 0)

    def test_create_device(self):
        self.assertEqual(Device.objects.all().count(), 0)
        response = self.client.post('/api/v1/devices/details/', {
            'name': 'Test',
            'devices_host_id': 'test',
            'type': 'sensor',
            'sensor_type': 'am2301'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.all().count(), 1)

    def test_get_devices(self):
        # create 10 devices
        for i in range(1, 11):
            device = Device(name='Test device %i' % i)
            device.save()
        response = self.client.get('/api/v1/devices/details/')
        json_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(json_response))

    def test_update_readings_for_multiple_devices(self):
        usr = User.objects.create_user(username='username2', password='password')
        # generate the token rather use JWT to check correct error
        token = Token.objects.create(user=usr)
        self.client.credentials(HTTP_AUTHORIZATION='Token {}'.format(token.key))
        Device.objects.create(name='Test', device_host_id='t1', type='relay', firmware='tasmota',
                              gpio=3)
        Device.objects.create(name='Test', device_host_id='t1', type='relay', firmware='tasmota',
                              gpio=2)
        data = [{
            'data': {
                'body': self.__convert_dict_to_base64({
                    "POWER2": "OFF"
                }),
                "properties": {
                    "topic": "t1/RESULT"
                },
            }
        }]
        response = self.client.post('/api/v1/devices/eventhub/', json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        # the device 1 should remain empty readings
        device1 = Device.objects.get(pk=1)
        self.assertEqual(device1.readings, None)

        # the device 2 should update its readings
        device2 = Device.objects.get(pk=2)
        self.assertEqual(device2.readings, {
            'state': 'OFF'
        })

    def test_update_multiple_readings_for_multiple_devices(self):
        # create 10 devices
        for i in range(1, 11):
            Device.objects.create(name='Test %i' % i, device_host_id='t1', type='relay', firmware='tasmota',
                                  gpio=i)

        # create multiple data
        data = [{
            'data': {
                'body': self.__convert_dict_to_base64({
                    "POWER10": "OFF"
                }),
                "properties": {
                    "topic": "t1/RESULT"
                },
            }
        }, {
            'data': {
                'body': self.__convert_dict_to_base64({
                    "POWER1": "ON",
                    'POWER2': 'ON',
                    'POWER3': 'ON'
                }),
                "properties": {
                    "topic": "t1/STATE"
                },
            }
        }]
        response = self.client.post('/api/v1/devices/eventhub/', json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # check the readings 10th device
        device = Device.objects.get(pk=10)
        self.assertEqual(device.readings, {'state': 'OFF'})

        # lets try does the second payload updated the readings for 3 devices
        for i in range(1, 4):
            dev = Device.objects.get(pk=i)
            self.assertEqual(dev.readings, {'state': 'ON'})

        # after the operation one log should be added
        self.assertEqual(len(DeviceLog.objects.all()), 1)

    def test_update_readings_to_relay(self):
        new_device = Device.objects.create(name='Test', device_host_id='wemos-t1', type='relay', firmware='tasmota',
                                           gpio=2)

        data = [{
            'data': {
                'body': self.__convert_dict_to_base64({
                    "POWER2": "OFF"
                }),
                "properties": {
                    "topic": "wemos-t1/RESULT"
                },
            }
        }]

        response = self.client.post('/api/v1/devices/eventhub/', json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        device = Device.objects.get(pk=new_device.pk)

        self.assertEqual(device.readings, {
            'state': 'OFF'
        })

        self.assertEqual(response.json(), {
            'msg': 'success',
        })
        # check log does it saved correctly
        logs = DeviceLog.objects.all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].readings, {
            'state': 'OFF'
        })

    def test_update_readings_to_sensor(self):
        device_1 = Device.objects.create(name='Test', device_host_id='wemos-t1', type='sensor', firmware='tasmota',
                                         sensor_type='am2301')
        payload = {
            "Time": "2021-08-16T13:57:26",
            "AM2301": {
                "DewPoint": 0,
                "Humidity": 44.4,
                "Temperature": 21.2
            },
            "TempUnit": "C"
        }
        data = [{
            'data': {
                'body': self.__convert_dict_to_base64(payload),
                "properties": {
                    "topic": "wemos-t1/SENSOR"
                },
            }
        }]

        response = self.client.post('/api/v1/devices/eventhub/', json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        device = Device.objects.get(pk=device_1.pk)

        self.assertEqual(device.readings, {
            'temperature': 21.2,
            'humidity': 44.4,
            'settings': {
                'tempUnits': 'C'
            }
        })

        # check logs it should be anything added
        self.assertEqual(len(DeviceLog.objects.all()), 0)

    def test_update_readings_expect_exception(self):
        data = {
            'data': {
                'body': '',
                "properties": {
                    "topic": "wemos-t1/SENSOR"
                },
            }
        }
        response = self.client.post('/api/v1/devices/eventhub/', json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 405)

    # def test_change_device_state(self):
    #     # @TODO mock it
    #     test_device = Device.objects.create(name='Test', device_host_id='wemos-t1', type='relay', firmware='tasmota',
    #                                         gpio=1)
    #     response = self.client.post('/api/v1/devices/device-state/%d/' % test_device.pk, {
    #         'state': 'on'
    #     })
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json(), {'result': 'OK'})

    def test_change_sensor_state(self):
        Device.objects.create(name='Test', device_host_id='wemos-t1', type='sensor', firmware='tasmota',
                              sensor_type='am2301')
        response = self.client.post('/api/v1/devices/device-state/1/', {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'You cannot send the message to sensor type'})

    def test_change_not_exist_device(self):
        response = self.client.post('/api/v1/devices/device-state/1/', {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})
