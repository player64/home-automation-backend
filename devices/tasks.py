# import os
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'backend.settings')
# import django
#
# django.setup()

from devices.models import Device, DeviceLog
from background_task import background


def sensor_tasks():
    """
    At every 30minutes save sensor reading to the database
    :return: None
    """
    sensors = Device.objects.filter(type='sensor')
    for sensor in sensors:
        if not sensor.readings:
            continue
        DeviceLog.objects.create(device=sensor, readings=sensor.readings)


@background(schedule=5)
def task_for_every_30_minutes():
    """
    At every 30minutes save sensor reading to the database
    :return: None
    """
    sensor_tasks()
