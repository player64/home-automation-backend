from django.test import TestCase

from devices.firmwareFactory import identify_firmware_by_payload_property


class TestsFirmwares(TestCase):

    def test_firmware_assign(self):
        test_payload = {
            'body': {
                'POWER1': 'OFF'
            },
            'properties': {
                'topic': 't1/RESULT'
            }
        }

        firmware_factory = identify_firmware_by_payload_property(test_payload['properties'])
        self.assertTrue(firmware_factory(test_payload['properties'], test_payload['body']).__str__(), 'tasmota')
