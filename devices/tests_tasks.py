from rest_framework.test import APITestCase

from devices.models import Device, DeviceLog
from devices.tasks import sensor_tasks


class TestTasks(APITestCase):

    def test_sensor_tasks(self):
        # add sensors
        for i in range(1, 21):
            # add readings to second device
            readings = {
                'temperature': 20 + i,
                'humidity': 50 + i
            } if i % 2 == 0 else None

            Device.objects.create(name='Sensor %i' % i, type='sensor', readings=readings)

        # run task
        sensor_tasks()
        logs = DeviceLog.objects.all()
        self.assertEqual(len(logs), 10)

