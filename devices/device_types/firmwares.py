from abc import ABC, abstractmethod

from devices.device_types.relays import RelayFactory


def identify_firmware_by_payload_property(payload_property: dict):
    if 'topic' in payload_property:
        return TasmotaFactory
    elif 'firmware' in payload_property:
        return ''


class FirmwareFactory(ABC):
    def __init__(self, properties: dict, body: dict):
        self.__properties = properties
        self.__body = body

    @abstractmethod
    def assign(self):
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

    def assign(self):
        topic = self.__parse_topic(self.properties['topic'])
        _actions = {
            'STATE': RelayFactory,
            # 'SENSOR': SensorFactory,
            'RESULT': RelayFactory,
        }

        return {
            'action': _actions[topic['type']] if topic['type'] in _actions else False,
            'device_id': topic['device_id']
        }

    @staticmethod
    def __parse_topic(topic):
        subject = topic.split('/')

        try:
            return {
                'device_id': subject[0],
                'type': subject[1]
            }
        except KeyError:
            return False

    def __str__(self):
        return 'tasmota'
