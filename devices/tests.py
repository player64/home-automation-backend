import base64
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import localtime
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from devices.models import Device, Workspace, EventHubMsg


class TestDevices(APITestCase):
    def __authenticate(self):
        User.objects.create_user(email='email@email.com', username='username', password='password')
        response = self.client.post('/api/v1/users/login/', {
            'username': 'username',
            'password': 'password'
        }, follow=True)
        token = response.json()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token['access']))

    def test_dashboard_with_no_workspaces(self):
        relay1 = Device(name='Test', device_host_id='t1', type='relay', firmware='tasmota', gpio=1)
        relay1.save()

        relay2 = Device(name='Test 2', device_host_id='t1', type='relay', firmware='tasmota', gpio=1)
        relay2.save()

        sensor = Device(name='Test 3', device_host_id='t1', type='sensor', firmware='tasmota', sensor_type='am2301')
        sensor.save()
        self.__authenticate()

        response = self.client.get('/api/v1/devices/dashboard/', follow=True)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue('devices' in content)
        self.assertTrue('workspaces' in content)
        self.assertEqual(len(content['devices']['relays']), 2)
        self.assertEqual(len(content['devices']['sensors']), 1)
        self.assertEqual(len(content['workspaces']), 0)

    def test_dashboard_with_workspaces(self):
        workspace = Workspace(name='Test workspace')
        workspace.save()

        workspace1 = Workspace(name='Test workspace2')
        workspace1.save()

        relay1 = Device(name='Test', device_host_id='t1', type='relay', firmware='tasmota', gpio=1, workspace=workspace)
        relay1.save()

        relay2 = Device(name='Test 2', device_host_id='t1', type='relay', firmware='tasmota',
                        gpio=1, workspace=workspace1)
        relay2.save()

        sensor = Device(name='Test 3', device_host_id='t1', type='sensor', firmware='tasmota',
                        sensor_type='am2301', workspace=workspace1)
        sensor.save()

        self.__authenticate()

        response = self.client.get('/api/v1/devices/dashboard/', follow=True)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('devices' in content)
        self.assertTrue('workspaces' in content)
        self.assertEqual(len(content['devices']['relays']), 1)
        self.assertEqual(len(content['devices']['sensors']), 0)
        self.assertEqual(len(content['workspaces']), 2)

        # check request with get parameters to receive devices from workspace 2
        response = self.client.get('/api/v1/devices/dashboard/?workspace=2', follow=True)
        content = response.json()
        self.assertEqual(len(content['devices']['relays']), 1)
        self.assertEqual(len(content['devices']['sensors']), 1)
        self.assertEqual(len(content['workspaces']), 2)

        # check unassigned devices should return all devices

        response = self.client.get('/api/v1/devices/dashboard/?workspace=none', follow=True)
        content = response.json()
        self.assertEqual(len(content['devices']['relays']), 2)
        self.assertEqual(len(content['devices']['sensors']), 1)
        self.assertEqual(len(content['workspaces']), 2)

    def test_get_workspace(self):
        workspace = Workspace(name='Test workspace')
        workspace.save()
        self.__authenticate()
        response = self.client.get('/api/v1/devices/workspace/%i/' % workspace.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['name'], 'Test workspace')

    def test_update_workspace(self):
        workspace = Workspace(name='Test workspace')
        workspace.save()
        self.__authenticate()
        response = self.client.put('/api/v1/devices/workspace/%i/' % workspace.pk, {
            'name': 'Test'
        })
        self.assertEqual(response.status_code, 200)
        ws = Workspace.objects.get(pk=1)
        self.assertEqual(ws.name, 'Test')

    def test_update_workspace_with_empty_name(self):
        workspace = Workspace(name='Test workspace')
        workspace.save()
        self.__authenticate()
        response = self.client.put('/api/v1/devices/workspace/%i/' % workspace.pk)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['name'][0], 'This field is required.')

    def test_delete_workspace(self):
        workspace = Workspace(name='Test workspace')
        workspace.save()
        self.assertEqual(Workspace.objects.all().count(), 1)
        self.__authenticate()
        response = self.client.delete('/api/v1/devices/workspace/%i/' % workspace.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Workspace.objects.all().count(), 0)

    def test_create_workspace(self):
        self.assertEqual(Workspace.objects.all().count(), 0)
        self.__authenticate()
        response = self.client.post('/api/v1/devices/workspaces/', {
            'name': 'Test'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Workspace.objects.all().count(), 1)

    def test_get_workspaces(self):
        # create 10 workspaces
        for i in range(1, 11):
            workspace = Workspace(name='Test workspace %i' % i)
            workspace.save()
        self.__authenticate()
        response = self.client.get('/api/v1/devices/workspaces/')
        json_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(json_response))

    # -----

    def test_get_device(self):
        device = Device(name='Test device', device_host_id='t1', type='relay', firmware='tasmota', gpio=1)
        device.save()
        self.__authenticate()
        response = self.client.get('/api/v1/devices/%i/' % device.pk)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['name'], 'Test device')

    def test_update_device(self):
        device = Device(name='Test device')
        device.save()
        self.__authenticate()
        response = self.client.put('/api/v1/devices/%i/' % device.pk, {
            'name': 'Test'
        })
        self.assertEqual(response.status_code, 200)
        ws = Device.objects.get(pk=1)
        self.assertEqual(ws.name, 'Test')

    def test_update_device_with_empty_name(self):
        device = Device(name='Test device')
        device.save()
        self.__authenticate()
        response = self.client.put('/api/v1/devices/%i/' % device.pk)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['name'][0], 'This field is required.')

    def test_delete_device(self):
        device = Device(name='Test device')
        device.save()
        self.assertEqual(Device.objects.all().count(), 1)
        self.__authenticate()
        response = self.client.delete('/api/v1/devices/%i/' % device.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Device.objects.all().count(), 0)

    def test_create_device(self):
        self.assertEqual(Device.objects.all().count(), 0)
        self.__authenticate()
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
        self.__authenticate()
        response = self.client.get('/api/v1/devices/details/')
        json_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(10, len(json_response))

    def test_update_readings_action_not_found(self):
        usr = User.objects.create_user(email='email@email.com', username='username', password='password')
        # generate the token rather use JWT to check correct error
        token = Token.objects.create(user=usr)
        self.client.credentials(HTTP_AUTHORIZATION='Token {}'.format(token.key))

        payload = {
            "Info1": {
                "Module": "Generic",
                "Version": "9.5.0.2(tasmota)",
            }
        }

        data = [{
            "data": {
                "body": self.__convert_dict_to_base64(payload),
                "properties": {
                    "topic": "wemos-t1/INFO1"
                },
            },
        }]

        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json',
                                    follow=True)
        self.assertEqual(response.status_code, 204)

    def test_update_readings_bad_data_type(self):
        self.__authenticate()
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps({}),
                                    content_type='application/json',
                                    follow=True)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'Request data must be a list'})

    def test_update_readings_key_error_exceptions(self):
        self.__authenticate()
        data = [{
            "data": {
                "test": "test",
            },
        }]
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json',
                                    follow=True)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'KeyError. Happened during assigning values body and properties'})

    def test_update_readings_firmware_not_found_exceptions(self):
        self.__authenticate()
        data = [{
            "data": {
                "body": self.__convert_dict_to_base64({'test': 'test'}),
                "properties": {},
            },
        }]
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json',
                                    follow=True)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'Firmware not found'})

    def test_update_readings_json_exception(self):
        self.__authenticate()
        data = [{
            "data": {
                "body": "",
                "properties": {
                    "topic": "d1"
                },
            },
        }]
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json',
                                    follow=True)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'Error when trying to convert body to json'})

    def test_update_readings_base64_decode_exception(self):
        self.__authenticate()
        data = [{
            "data": {
                "body": "jnjdfiojfiodjoifjoifjo",
                "properties": {
                    "topic": "d1"
                },
            },
        }]
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json',
                                    follow=True)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'Error when trying to decode body to ascii'})

    def test_update_readings_device_readings_not_updated(self):
        self.__authenticate()
        Device.objects.create(name='Test', device_host_id='t1', type='relay', firmware='tasmota',
                              gpio=3)
        Device.objects.create(name='Test', device_host_id='t1', type='relay', firmware='tasmota',
                              gpio=2)
        payload = {
            "POWER2": "OFF"
        }
        data = [{
            'data': {
                'body': self.__convert_dict_to_base64(payload),
                "properties": {
                    "topic": "t1/RESULT"
                },
            }
        }]
        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)


    def test_status_to_relay(self):
        self.__authenticate()
        Device.objects.create(name='Test', device_host_id='wemos-t1', type='relay', firmware='tasmota',
                              gpio=2)
        payload = {
            "POWER2": "OFF"
        }
        data = [{
            'data': {
                'body': self.__convert_dict_to_base64(payload),
                "properties": {
                    "topic": "wemos-t1/RESULT"
                },
            }
        }]

        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        device = Device.objects.get(pk=device_1.pk)

        self.assertEqual(device.readings, {
            'state': 'OFF'
        })

        self.assertEqual(response.json(), {
            'msg': 'success',
            'data': {
                "POWER2": "OFF"
            },
        })

    def test_status_to_sensor(self):
        self.__authenticate()
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

        response = self.client.post('/api/v1/devices/update-readings/', json.dumps(data),
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

    @staticmethod
    def __convert_dict_to_base64(payload: dict):
        payload_json = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(payload_json).decode()

    def test_change_device_state(self):
        test_device = Device.objects.create(name='Test', device_host_id='wemos-t1', type='relay', firmware='tasmota',
                                            gpio=1)
        self.__authenticate()
        response = self.client.post('/api/v1/devices/device-state/%d/' % test_device.id, {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'result': 'OK'})

    def test_change_sensor_state(self):
        test_device = Device.objects.create(name='Test', device_host_id='wemos-t1', type='sensor', firmware='tasmota',
                                            sensor_type='am2301')
        self.__authenticate()
        response = self.client.post('/api/v1/devices/device-state/%d/' % test_device.id, {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'You cannot send the message to sensor type'})

    def test_change_not_exist_device(self):
        self.__authenticate()
        response = self.client.post('/api/v1/devices/device-state/%d/' % 1, {
            'state': 'on'
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})
