from devices.device_types.abstracts import DeviceTypeFactory, FirmwareFactory
from devices.device_types.tasmota import RelayTasmota, AM2301Tasmota, TasmotaFactory
from devices.device_types.exceptions import DeviceExceptions


def identify_by_payload(payload_property: dict) -> FirmwareFactory:
    if 'topic' in payload_property:
        return TasmotaFactory
    raise NotImplementedError("Firmware not found")


class RelayFactory(DeviceTypeFactory):
    def obtain_factory(self):
        factories = {
            'tasmota': RelayTasmota,
            # other firmware types
        }

        try:
            relay_factory = factories[self.device.firmware]
        except KeyError:
            raise DeviceExceptions('Relay factory not found')

        return relay_factory


class SensorFactory(DeviceTypeFactory):
    def obtain_factory(self):
        sensor_types = {
            'am2301': AM2302Factory,
            # other factories
        }
        try:
            factory = sensor_types[self.device.sensor_type]
        except KeyError:
            raise DeviceExceptions('Sensor factory not found in SensorFactory')
        return factory().obtain_factory(self.device.firmware)

    def __repr__(self):
        return 'SensorFactory'


class AM2302Factory:
    def obtain_factory(self, firmware_type):
        sensor_types = {
            'tasmota': AM2301Tasmota,
            # other firmware types
        }
        try:
            am2301 = sensor_types[firmware_type]
        except KeyError:
            raise DeviceExceptions('Firmware AM2301 not found in AM2302Factory')
        return am2301
