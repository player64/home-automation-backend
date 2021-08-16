import json
from abc import ABC, abstractmethod
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'backend.settings')
import django

django.setup()
from devices.models import Device


class FirmwareIdentifier:
    @classmethod
    def identify(cls,  payload_property: dict):
        if 'topic' in payload_property:
            return TasmotaFactory
        elif 'firmware' in payload_property:
            return SimulatedFactory
        else:
            raise NotImplementedError("Firmware not found")


class FirmwareFactory(ABC):
    def __init__(self, properties: dict, body: dict):
        try:
            self.__properties = properties
            self.__body = body
        except Exception as a:
            print(a)

    @abstractmethod
    def identify(self):
        pass

    @property
    def properties(self):
        return self.__properties

    @property
    def body(self):
        return self.__body

    def __str__(self):
        pass


class TasmotaFactory(FirmwareFactory):
    def identify(self):
        properties = self.properties
        subject = properties['topic']
        types = subject.split('/')
        _types = {
            'STATE': RelayFactory,
            'SENSOR': SensorFactory,
            'RESULT': RelayFactory
        }

        return {
            'device_id': types[0],
            'factory': _types[types[1]] if types[1] in _types else False
        }

    def __str__(self):
        return 'tasmota'


class SimulatedFactory(FirmwareFactory):
    def identify(self):
        pass

    def __str__(self):
        return 'simulated'


# ------------------------------------
class AbstractDevice(ABC):
    def __init__(self, firmware: FirmwareFactory, device: Device):
        self.__firmware = firmware
        self.__device = device

    @property
    def firmware(self):
        return self.__firmware

    @property
    def device(self):
        return self.__device

    @abstractmethod
    def get_readings(self):
        pass

    @abstractmethod
    def message(self):
        pass

    def get_factory_type(self):
        factories = {
            'sensor': SensorFactory,
            'relay': RelayFactory
        }
        return factories.get(self.firmware.identify()['reading_type'], lambda: 'Wrong argument')


class RelayFactory:

    def __init__(self, device: Device):
        self.Device = device

    def obtain(self):
        switcher = {
            'tasmota': RelayTasmota,
            'simulated': RelaySimulated
        }
        relay = switcher.get(self.Device.firmware, lambda: 'Wrong argument')
        return relay


class RelayTasmota(AbstractDevice):
    def get_readings(self):
        body = self.firmware.body
        return {
            'state': body['POWER{}'.format(self.device.gpio)]
        }

    def message(self):
        pass


class RelaySimulated(AbstractDevice):
    def get_readings(self):
        pass

    def message(self):
        pass


class SensorFactory:

    def __init__(self, device: Device):
        self.Device = device

    def obtain(self):
        sensor_types = {
            'am2301': AM2302Factory,
            # other factories
        }
        factory = sensor_types.get(self.Device.sensor_type, lambda: 'Wrong argument')
        return factory().obtain(self.Device.firmware)


class AM2302Factory:
    def obtain(self, firmware_type):
        switcher = {
            'tasmota': AM2301Tasmota,
            'simulated': AM2301Simulated
        }
        am2301 = switcher.get(firmware_type, lambda: 'Wrong argument')
        return am2301


class AM2301Tasmota(AbstractDevice):
    def get_readings(self):
        body = self.firmware.body
        return {
            'temperature': body['AM2301']['Temperature'],
            'humidity': body['AM2301']['Humidity'],
            'tempUnits': body['TempUnit']
        }

    def message(self):
        pass


class AM2301Simulated(AbstractDevice):
    def get_readings(self):
        body = self.firmware.body
        return {
            'temperature': body['temperature'],
            'humidity': body['humidity'],
            'tempUnits': body['units']
        }

    def message(self):
        pass
