from abc import ABC, abstractmethod


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
