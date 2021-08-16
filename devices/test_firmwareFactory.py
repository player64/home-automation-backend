from datetime import datetime
import json
from django.test import TestCase

from devices.firmwareFactory import FirmwareIdentifier, TasmotaFactory, AM2302Factory, RelayFactory, SensorFactory
from devices.models import Device


class TestFirmwareFactory(TestCase):
    def am2302TasmotaBody(self):
        return {
            "AM2301": {
                "DewPoint": 22,
                "Humidity": 44,
                "Temperature": 28
            },
            "TempUnit": "C",
            "Time": "2021-08-10T18:20:39"
        }

    def am2302SimulatedBody(self):
        return {
            'sensor_type': 'AM2301',
            "humidity": 44,
            "temperature": 28,
            "units": 'F'
        }

    def relayTasmotaBody(self):
        return {
            "POWER1": "OFF",
            "POWER2": "ON",
        }

    def propertiesTasmotaMsg(self, type_topic):
        return {
            'topic': 't1/%s' % type_topic
        }

    def test_firmware_identity(self):
        properties = self.propertiesTasmotaMsg('SENSOR')

        firmware_identifier = FirmwareIdentifier(properties)
        firmware_factory = firmware_identifier.identify()
        body = self.am2302TasmotaBody()
        firmware_factory = firmware_factory(properties, body)

        self.assertEqual(firmware_factory.__str__(), 'tasmota')
        self.assertEqual(firmware_factory.identify()['device_id'], 't1')
        # print(firmware_factory.identify()['factory'])
        # self.assertTrue(isinstance(firmware_factory.identify()['factory'], SensorFactory))

    def test_am_sensor_readings(self):
        device = Device(
            name='Test',
            device_host_id='t1',
            type='sensor',
            firmware='tasmota',
            sensor_type='am2301'
        )

        properties = self.propertiesTasmotaMsg('SENSOR')
        body = self.am2302TasmotaBody()
        firmware = TasmotaFactory(properties, body)
        sensor_factory = AM2302Factory()
        sensor = sensor_factory.obtain(firmware.__str__())
        sensor = sensor(firmware, device)

        self.assertEqual(sensor.get_readings(), {
            'temperature': 28,
            'humidity': 44,
            'tempUnits': 'C'
        })

    def test_relay_readings(self):
        new_device = Device(
            name='Test',
            device_host_id='t1',
            type='relay',
            gpio=2,
        )

        properties = self.propertiesTasmotaMsg('STATE')
        body = self.relayTasmotaBody()
        firmware_identifier = FirmwareIdentifier(properties)
        firmware_factory = firmware_identifier.identify()
        firmware_factory = firmware_factory(properties, body)
        self.assertEqual(firmware_factory.__str__(), 'tasmota')

        message_identify = firmware_factory.identify()

        if message_identify['reading_type'] == 'sensor':
            device_factory = SensorFactory(new_device)
        elif message_identify['reading_type'] == 'relay':
            device_factory = RelayFactory(new_device)

        device = device_factory.obtain()
        relay = device(firmware_factory, new_device)

        self.assertEqual(relay.get_readings(), {
            'state': 'ON'
        })

        new_device.readings = relay.get_readings()
        new_device.save()
        db_device = Device.objects.filter(pk=new_device.id)
        self.assertEqual(db_device[0].readings, {
            'state': 'ON'
        })

    def test_sensor_readings(self):
        new_device = Device(
            name='Test',
            device_host_id='t1',
            type='sensor',
            sensor_type='am2301',
        )

        properties = self.propertiesTasmotaMsg('SENSOR')
        body = self.am2302TasmotaBody()
        firmware_instance = FirmwareIdentifier.identify(properties)
        firmware_factory = firmware_instance(properties, body)
        self.assertEqual(firmware_factory.__str__(), 'tasmota')

        device_factory_type = firmware_factory.identify()
        device_factory_instance = device_factory_type['factory']

        factory_device_type = device_factory_instance(new_device)
        type_factory = factory_device_type.obtain()
        obtained_device = type_factory(firmware_factory, new_device)

        self.assertEqual(obtained_device.get_readings(), {
            'temperature': 28,
            'humidity': 44,
            'tempUnits': 'C'
        })

        new_device.readings = obtained_device.get_readings()
        new_device.updated_at = datetime.today()
        new_device.save()
        db_device = Device.objects.filter(pk=new_device.id)
        self.assertEqual(db_device[0].readings, {
            'temperature': 28,
            'humidity': 44,
            'tempUnits': 'C'
        })
