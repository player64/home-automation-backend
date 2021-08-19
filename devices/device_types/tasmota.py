import os

from devices.device_types.abstracts import FirmwareFactory, FirmwareIdentifyProperties, AbstractDevice
from devices.device_types import device_type_factories
from devices.device_types.exceptions import FirmwareFactoryException, DeviceExceptions
from azure.iot.hub import IoTHubRegistryManager


class TasmotaFactory(FirmwareFactory):
    def identify_properties(self) -> FirmwareIdentifyProperties:
        try:
            subject = self.properties['topic']
            types = subject.split('/')
            host_device_id = types[0]
            action = types[1]
        except KeyError:
            raise FirmwareFactoryException('Error when parse the device identify')

        _action_types = {
            'STATE': device_type_factories.RelayFactory,
            'SENSOR': device_type_factories.SensorFactory,
            'RESULT': device_type_factories.RelayFactory
        }

        try:
            factory = _action_types[action]
        except KeyError:
            raise FirmwareFactoryException('Action not found in TasmotaFactory')

        return {
            'device_id': host_device_id,
            'factory': factory,
            'save_to_log': (action == 'RESULT')
        }

    def __str__(self):
        return 'tasmota'


class RelayTasmota(AbstractDevice):
    def get_readings(self):
        body = self.firmware.body
        try:
            state = body['POWER%i' % self.device.gpio]
            return {
                'state': state
            }
        except KeyError:
            raise DeviceExceptions('Cannot read the readings from tasmota relay')

    def message(self, state: str):
        """
        Method used to enable / disable device
        :param state: on or off
        :return: None
        """
        connection_secret = os.environ.get('CONNECTION_STRING')
        if not connection_secret:
            raise DeviceExceptions('You must provide Azure CONNECTION_STRING secret')
        registry_manager = IoTHubRegistryManager(connection_secret)
        props = {}
        props.update(TOPIC='/power%d' % self.device.gpio)
        registry_manager.send_c2d_message(self.device.device_host_id, state, properties=props)


class AM2301Tasmota(AbstractDevice):
    def get_readings(self):
        body = self.firmware.body

        try:
            temperature = body['AM2301']['Temperature']
            humidity = body['AM2301']['Humidity']
            temp_units = body['TempUnit']
        except KeyError:
            raise DeviceExceptions('Cannot read the readings from tasmota AM2301')

        return {
            'temperature': temperature,
            'humidity': humidity,
            'settings': {
                'tempUnits': temp_units
            }
        }

    def message(self, msg):
        raise DeviceExceptions('You cannot send the message to sensor type')
