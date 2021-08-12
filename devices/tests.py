import json

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase
from devices.models import Device, Workspace


class TestDevices(APITestCase):
    def __authenticate(self):
        User.objects.create_user(email='email@email.com', username='username', password='password')
        response = self.client.post('/api/v1/login/', {
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

        # check get parameters to receive devices from workspace 2
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