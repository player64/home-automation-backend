import os

from devices.device_types.abstracts import FirmwareFactory, FirmwareIdentifyProperties, AbstractDevice
from devices.device_types import device_type_factories
from devices.device_types.exceptions import FirmwareFactoryException, DeviceException
from azure.iot.hub import IoTHubRegistryManager


class TasmotaFactory(FirmwareFactory):
    def identify_payload(self) -> FirmwareIdentifyProperties:
        """
        Method used to parse the message from Azure IoT Hub sent by Tasmota device
        :return: {
            'device_id': str
            'factory': DeviceTypeFactory,
            'save_to_log': bool
        }
        """
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
            return {
                'device_id': host_device_id,
                'factory': factory,
                'save_to_db': (action == 'RESULT')
            }
        except KeyError:
            raise FirmwareFactoryException('Action not found in TasmotaFactory')


    def __str__(self):
        return 'tasmota'


class RelayTasmota(AbstractDevice):
    def get_readings(self):
        """
        Method for getting readings from Azure IoT Hub reads them from Tasmota firmware
        :return: {'state': ON or OFF}
        """
        body = self.firmware.body
        try:
            return {
                'state': body['POWER%i' % self.device.gpio]
            }
        except KeyError:
            raise DeviceException('Cannot read the readings from tasmota relay')
        except TypeError:
            raise DeviceException('GPIO is None type')

    def message(self, state: str):
        """
        Method used to enable / disable device
        :param state: on or off
        :return: None
        """
        connection_secret = os.environ.get('CONNECTION_STRING')
        if not connection_secret:
            raise DeviceException(
                'Azure CONNECTION_STRING secret not found. Add CONNECTION_STRING to your environment.')
        registry_manager = IoTHubRegistryManager(connection_secret)
        props = {}
        props.update(TOPIC='/power%d' % self.device.gpio)
        registry_manager.send_c2d_message(self.device.device_host_id, state, properties=props)


class AM2301Tasmota(AbstractDevice):
    def get_readings(self):
        """
        Method for getting readings from Azure IoT Hub reads them from Tasmota firmware
        :return: {
                'temperature': float,
                'humidity': float,
                'settings': {
                    'tempUnits': C or F
                }
            }
        """
        body = self.firmware.body
        try:
            return {
                'temperature': body['AM2301']['Temperature'],
                'humidity': body['AM2301']['Humidity'],
                'settings': {
                    'tempUnits': body['TempUnit']
                }
            }
        except KeyError:
            raise DeviceException('Cannot read the readings from tasmota AM2301')

    def message(self, msg=None):
        """
        Mathod not implemented
        :param msg: None
        :return: DeviceException
        """
        raise DeviceException('You cannot send the message to sensor type')
