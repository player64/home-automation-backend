from abc import ABC, abstractmethod
from typing import TypedDict

from devices.models import Device


class DeviceTypeFactory(ABC):
    def __init__(self, device: Device):
        self.__device = device

    @abstractmethod
    def obtain_factory(self):
        pass

    @property
    def device(self):
        return self.__device


class FirmwareIdentifyProperties(TypedDict):
    device_id: str
    factory: DeviceTypeFactory
    save_to_db: bool


class FirmwareFactory(ABC):
    def __init__(self, properties: dict, body: dict):
        self.__properties: dict = properties
        self.__body: dict = body

    @abstractmethod
    def identify_payload(self) -> FirmwareIdentifyProperties:
        pass

    @property
    def properties(self):
        return self.__properties

    @property
    def body(self):
        return self.__body

    def __str__(self):
        pass


class AbstractDevice(ABC):
    def __init__(self, firmware: FirmwareFactory or None, device: Device):
        self.__firmware = firmware
        self.__device = device

    @property
    def firmware(self) -> FirmwareFactory:
        return self.__firmware

    @property
    def device(self) -> Device:
        return self.__device

    @abstractmethod
    def get_readings(self) -> dict:
        pass

    @abstractmethod
    def message(self, msg):
        pass
