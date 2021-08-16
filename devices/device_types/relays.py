from devices.models import Device


class RelayFactory:

    Device = None

    def __init__(self, device: Device):
        self.Device = device

    @classmethod
    def get_type(cls):
        device_firmware = cls.Device.firmware
        return cls.__relays_type()[device_firmware](cls.Device) if device_firmware in cls.__relays_type() else False

    @staticmethod
    def __relays_type():
        return {
            'tasmota': RelayTasmota
        }


class RelayTasmota:
    def __init__(self, device: Device):
        self.device = device

    def get_readings(self):
        pass
