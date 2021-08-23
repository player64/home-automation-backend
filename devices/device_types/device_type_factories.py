from devices.device_types.abstracts import DeviceTypeFactory, FirmwareFactory
from devices.device_types.tasmota import RelayTasmota, AM2301Tasmota, TasmotaFactory
from devices.device_types.exceptions import DeviceException


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
            return relay_factory
        except KeyError:
            raise DeviceException('Relay factory not found')


class SensorFactory(DeviceTypeFactory):
    def obtain_factory(self):
        sensor_types = {
            'am2301': AM2302Factory,
            # other factories
        }
        try:
            factory = sensor_types[self.device.sensor_type]
            return factory().obtain_factory(self.device.firmware)
        except KeyError:
            raise DeviceException('Sensor factory not found in SensorFactory; Sensor Type: %s; Firmware: %s' % (
                self.device.sensor_type, self.device.firmware))

    def __repr__(self):
        return 'SensorFactory'


class AM2302Factory:
    def obtain_factory(self, firmware_type):
        sensor_types = {
            'tasmota': AM2301Tasmota,
            # other firmware types
        }
        try:
            return sensor_types[firmware_type]
        except KeyError:
            raise DeviceException('Firmware AM2301 not found in AM2302Factory')
