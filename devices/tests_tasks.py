import json
from unittest.mock import patch
from django.test import TestCase
from django.utils.datetime_safe import datetime
from devices.models import Device, DeviceLog, DeviceEvent
from devices.tasks import sensor_periodic_tasks, time_relay_task, is_event_time, \
    is_eligible_to_fire_task_based_on_readings, get_sensor_reading_type, sensor_rule_task


def mock_time_return(hour: int, minute: int):
    return datetime(hour=hour, minute=minute, day=1, month=1, year=2021)


def create_device(readings: dict or None, device_type='relay') -> Device:
    device = Device(name='Test', device_host_id='t1', type=device_type,
                    readings=json.dumps(readings) if readings else None)
    if device_type == 'relay':
        device.gpio = 1
    elif device_type == 'sensor':
        device.sensor_type = 'am2301'
    device.save()
    return device


class TestTask(TestCase):
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
        sensor_periodic_tasks()
        logs = DeviceLog.objects.all()
        self.assertEqual(len(logs), 10)

    @patch.object(datetime, 'now')
    def test_is_event_time(self, mock_time_now):
        mock_time_now.return_value = mock_time_return(18, 30)
        device = create_device(None)
        task = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                          action='ON', time=mock_time_return(18, 30))

        task2 = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time=mock_time_return(18, 31))

        self.assertTrue(is_event_time(task.time))
        self.assertFalse(is_event_time(task2.time))

    def test_is_eligible_to_fire_task_based_on_readings(self):
        device = create_device(None)
        device2 = create_device({
            'state': 'on'
        })
        event1 = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                            action='ON', time='18:30')
        event2 = DeviceEvent.objects.create(name='Event', device=device2, type='time',
                                            action='ON', time='18:30')
        self.assertTrue(is_eligible_to_fire_task_based_on_readings(event1))
        self.assertFalse(is_eligible_to_fire_task_based_on_readings(event2))

    def test_is_eligible_to_fire_task_error_readings(self):
        device = create_device({'test': 'test'})
        event = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time='18:30')
        self.assertFalse(is_eligible_to_fire_task_based_on_readings(event))

    def test_is_eligible_to_fire_task_based_on_json_non_serializable(self):
        device = Device.objects.create(name='Test', device_host_id='t1', type='relay', readings='test_faulty')
        event = DeviceEvent.objects.create(name='Event', device=device, type='time',
                                           action='ON', time='18:30')
        self.assertFalse(is_eligible_to_fire_task_based_on_readings(event))

    def test_get_sensor_reading(self):
        sensor = create_device({
            'temperature': 22.8,
            'humidity': 68.7
        }, 'sensor')

        self.assertEqual(get_sensor_reading_type(sensor, 'temperature'), 22.8)

    def test_get_sensor_reading_with_incorrect_key(self):
        sensor = create_device({
            'temperature': 22.8,
            'humidity': 68.7
        }, 'sensor')

        self.assertEqual(get_sensor_reading_type(sensor, 'test'), None)

    def test_get_sensor_reading_with_corrupted_readings(self):
        sensor = Device.objects.create(name='Test', device_host_id='t1', type='sensor', readings='test_faulty')
        self.assertEqual(get_sensor_reading_type(sensor, 'test'), None)

    def test_sensor_rule_task(self):
        self.assertTrue(sensor_rule_task('>', 25.3, 23.1))
        self.assertFalse(sensor_rule_task('>', 22.3, 23.1))

        self.assertTrue(sensor_rule_task('<', 25.3, 26.1))
        self.assertFalse(sensor_rule_task('<', 22.3, 21.1))

    def test_sensor_rule_task_wrong_rule(self):
        self.assertFalse(sensor_rule_task('test', 22, 21))


@patch('azure.iot.hub.IoTHubRegistryManager.send_c2d_message', return_value='')
@patch('os.environ.get', return_value='HostName=test;SharedAccessKeyName=test;SharedAccessKey=test')
class TestFireTasks(TestCase):
    """
    Methods in the class uses mocks to send message to devices
    """

    @patch.object(datetime, 'now')
    def test_time_relay_task(self, mock_time_now, mock_azure, mock_connection_key):
        mock_time_now.return_value = mock_time_return(18, 30)
        for i in range(0, 10):
            device = create_device({'state': 'off'})
            DeviceEvent.objects.create(name='Event', device=device, type='time',
                                       action='ON', time='18:3%i' % i)
        fired_tasks = time_relay_task()
        self.assertEqual(len(fired_tasks), 1)
        self.assertEqual(fired_tasks[0], 'ON')

    @patch.object(datetime, 'now')
    def test_time_relay_task_with_same_state(self, mock_time_now, mock_azure, mock_connection_key):
        mock_time_now.return_value = mock_time_return(18, 30)
        device = create_device({'state': 'on'})
        DeviceEvent.objects.create(name='Event', device=device, type='time',
                                   action='ON', time='18:30')
        fired_tasks = time_relay_task()
        self.assertEqual(len(fired_tasks), 0)

    @patch.object(datetime, 'now')
    def test_time_relay_task_with_no_readings(self, mock_time_now, mock_azure, mock_connection_key):
        mock_time_now.return_value = mock_time_return(18, 30)
        device = Device.objects.create(name='Test', device_host_id='t1', type='relay', gpio=1)
        DeviceEvent.objects.create(name='Event', device=device, type='time',
                                   action='ON', time='18:30')
        fired_tasks = time_relay_task()
        self.assertEqual(len(fired_tasks), 1)
