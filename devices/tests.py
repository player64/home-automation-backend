import base64
import json
import os
from datetime import datetime
from unittest.mock import patch

from azure.iot.hub import IoTHubRegistryManager
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
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

        # add some other logs with the past date
        for i in range(1, 30):
            _date = '2021-05-%d 19:00:00' % i
            log1 = DeviceLog.objects.create(device=device, readings={'state': 'OFF'})
            # rewrite date
            log1.time = make_aware(datetime.strptime(_date, '%Y-%m-%d %H:%M:%S'))
            log1.save()

        # add one log to check filter is working as expected
        other_dev = Device(name='Test device', device_host_id='t1')
        other_dev.save()
        DeviceLog.objects.create(readings={'state': 'OFF'}, device=other_dev)

        response = self.client.get('/api/v1/devices/single/%i/' % device.pk)
        content = response.json()
        self.assertEqual(content['workspace']['name'], 'Workspace')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['name'], 'Test device')

    def test_get_device_with_events(self):
        device = Device.objects.create(name='Test device', device_host_id='t1',
                                       type='relay', firmware='tasmota', gpio=1)
        device2 = Device.objects.create(name='Test device 2', device_host_id='t1',
                                       type='relay', firmware='tasmota', gpio=3)
        # add five events
        for i in range(1, 6):
            DeviceEvent.objects.create(name='Event%d' % i, device=device, type='time',
                                       action='ON', time='18:30')
            DeviceEvent.objects.create(name='Event for device 2 %d' % i, device=device2, type='time',
                                       action='ON', time='18:30')

        response = self.client.get('/api/v1/devices/events/%i/' % device.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    def test_update_device_with_workspace(self):
        w = Workspace.objects.create(name='Workspace')
        device = Device(name='Test device')
        device.save()
        response = self.client.put('/api/v1/devices/%i/' % device.pk, {
            'name': 'Test',
            'device_host_id': 'test',
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
            'device_host_id': 'test',
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

    def test_get_devices_by_type(self):
        # create 10 devices each
        for i in range(1, 11):
            Device.objects.create(name='Test relay %i' % i, type='relay')
            Device.objects.create(name='Test sensor %i' % i, type='sensor')
        response = self.client.get('/api/v1/devices/details/?type=sensor')
        json_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(json_response))

    def test_search_devices(self):
        names = ['Device', 'Sensor', 'Relay1', 'Relay2', 'Relay3']
        for name in names:
            Device.objects.create(name=name, type='relay')
        response = self.client.get('/api/v1/devices/search/?name=re')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_search_with_one_character(self):
        response = self.client.get('/api/v1/devices/search/?name=k')
        self.assertEqual(response.status_code, 400)

    def test_get_device_readings(self):
        readings = {
            'state': 'ON'
        }
        _date = '2021-08-24 10:00:00'
        updated_at = make_aware(datetime.strptime(_date, '%Y-%m-%d %H:%M:%S'))
        device = Device.objects.create(name='Test Relay', readings=readings, updated_at=updated_at)
        response = self.client.get('/api/v1/devices/readings/%i/' % device.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['readings'], readings)
        self.assertEqual(content['updated_at'], str(updated_at).replace(' ', 'T'))

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
        # create 10 relays and sensors
        for i in range(1, 11):
            Device.objects.create(name='Test relay %i' % i, device_host_id='t1', type='relay', gpio=i)

        for i in range(1, 11):
            Device.objects.create(name='Test sensor %i' % i, device_host_id='t1', type='sensor', sensor_type='am2301')

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

        # add more devices relays
        for i in range(0, 7):
            Device.objects.create(name='Test device relay', gpio=i, device_host_id='wemos-t1', type='relay')

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

    @patch.object(IoTHubRegistryManager, 'send_c2d_message')
    @patch.object(os.environ, 'get')
    def test_change_device_state(self, mock_env_connection_string, mock_send_c2d_message):
        # keep this key format otherwise will throw exception
        mock_env_connection_string.return_value = 'HostName=test;SharedAccessKeyName=test;SharedAccessKey=test'
        mock_send_c2d_message.return_value = ''
        test_device = Device.objects.create(name='Test', device_host_id='test', type='relay',
                                            gpio=1)
        response = self.client.post('/api/v1/devices/device-state/%d/' % test_device.pk, {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'state': 'on'})

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
