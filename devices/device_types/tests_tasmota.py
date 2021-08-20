import re

from django.test import TestCase

from devices.device_types.device_type_factories import identify_by_payload
from devices.device_types.tasmota import TasmotaFactory, RelayTasmota
from devices.device_types.exceptions import FirmwareFactoryException, DeviceException
from devices.models import Device


class TestTasmota(TestCase):
    @staticmethod
    def body(body_type: str) -> dict:
        _types = {
            'am2301': {
                "AM2301": {
                    "DewPoint": 22,
                    "Humidity": 44,
                    "Temperature": 28
                },
                "TempUnit": "C",
                "Time": "2021-08-10T18:20:39"
            },
            'relay': {
                "POWER1": "OFF",
                "POWER2": "ON",
            }
        }
        return _types[body_type]

    @staticmethod
    def properties(type_topic: str) -> dict:
        return {
            'topic': 't1/%s' % type_topic
        }

    def test_identity_properties(self):
        properties = self.properties('RESULT')
        firmware = identify_by_payload(properties)
        firmware_factory = firmware(properties, {})
        identify = firmware_factory.identify_properties()

        self.assertEqual(str(firmware_factory), 'tasmota')
        self.assertEqual(identify['device_id'], 't1')
        self.assertTrue(re.search(r'\bRelayFactory\b', str(identify['factory'])))
        self.assertTrue(identify['save_to_db'])

    def test_identify_parse_error(self):
        with self.assertRaises(FirmwareFactoryException) as context:
            tasmota = TasmotaFactory({'test': 'test'}, {})
            tasmota.identify_properties()
        self.assertEqual(str(context.exception), 'Error when parse the device identify')

    def test_identify_action_not_found(self):
        with self.assertRaises(FirmwareFactoryException) as context:
            tasmota = TasmotaFactory(self.properties('INFO'), {})
            tasmota.identify_properties()
        self.assertEqual(str(context.exception), 'Action not found in TasmotaFactory')

    def test_relay_readings(self):
        properties = self.properties('STATE')
        body = self.body('relay')
        firmware = identify_by_payload(properties)
        firmware_factory = firmware(properties, body)
        identify = firmware_factory.identify_properties()

        # set relay device
        test_device = Device(
            name='Test',
            device_host_id='t1',
            type='relay',
            gpio=2,
        )

        device_type_factory_instance = identify['factory']
        device_type_factory = device_type_factory_instance(test_device).obtain_factory()
        device = device_type_factory(firmware_factory, test_device)

        self.assertEqual(device.get_readings(), {
            'state': 'ON'
        })

    def test_relay_exception(self):
        test_device = Device(
            name='Test',
            device_host_id='t1',
            type='relay',
            gpio=4,
        )
        firmware = TasmotaFactory(self.properties('STATE'), self.body('relay'))
        relay = RelayTasmota(firmware, test_device)
        with self.assertRaises(DeviceException) as context:
            relay.get_readings()
        self.assertEqual(str(context.exception), 'Cannot read the readings from tasmota relay')

    def test_sensor_readings(self):
        properties = self.properties('SENSOR')
        body = self.body('am2301')
        firmware = identify_by_payload(properties)
        firmware_factory = firmware(properties, body)
        identify = firmware_factory.identify_properties()

        self.assertEqual(identify['device_id'], 't1')
        self.assertTrue(re.search(r'\bSensorFactory\b', str(identify['factory'])))
        self.assertFalse(identify['save_to_db'])

        # set relay device
        test_device = Device(
            name='Test',
            device_host_id='t1',
            type='sensor',
            sensor_type='am2301',
        )

        device_type_factory_instance = identify['factory']
        device_type_factory = device_type_factory_instance(test_device).obtain_factory()
        device = device_type_factory(firmware_factory, test_device)
        self.assertEqual(device.get_readings(), {
            'temperature': 28,
            'humidity': 44,
            'settings': {
                'tempUnits': 'C'
            }
        })

    def test_sensor_factory_exception(self):
        properties = self.properties('SENSOR')
        body = self.body('am2301')
        firmware = TasmotaFactory(properties, body)
        identify = firmware.identify_properties()
        test_device = Device(
            name='Test',
            device_host_id='t1',
            type='sensor',
            sensor_type='tests',
        )
        device_type_factory_instance = identify['factory']
        with self.assertRaises(DeviceException) as context:
            device_type_factory_instance(test_device).obtain_factory()
        self.assertEqual(str(context.exception), 'Sensor factory not found in SensorFactory')

    def test_sensor_firmware_exception(self):
        properties = self.properties('SENSOR')
        body = self.body('am2301')
        test_device = Device(
            name='Test',
            device_host_id='t1',
            firmware='something_else',
            type='sensor',
            sensor_type='am2301',
        )
        firmware = TasmotaFactory(properties, body)
        identify = firmware.identify_properties()
        device_type_factory_instance = identify['factory']
        with self.assertRaises(DeviceException) as context:
            device_type_factory_instance(test_device).obtain_factory()
        self.assertEqual(str(context.exception), 'Firmware AM2301 not found in AM2302Factory')
