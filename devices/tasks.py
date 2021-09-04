# import os
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'backend.settings')
# import django
#
# django.setup()
import json

from django.utils.datetime_safe import datetime

from devices.device_types.device_type_factories import RelayFactory
from devices.device_types.exceptions import DeviceException
from devices.models import Device, DeviceLog, DeviceEvent
from background_task import background
import logging

logger = logging.getLogger('django')


def sensor_periodic_tasks():
    """
    At every hour save sensor reading saves to the database
    :return: None
    """
    sensors = Device.objects.filter(type='sensor')
    for sensor in sensors:
        if not sensor.readings:
            continue
        DeviceLog.objects.create(device=sensor, readings=sensor.readings)


def is_event_time(event_time: datetime) -> bool:
    now = datetime.now()
    return now.hour == event_time.hour and now.minute == event_time.minute


def is_eligible_to_fire_task_based_on_readings(task: DeviceEvent) -> bool:
    if not task.device.readings:
        return True
    try:
        readings = json.loads(task.device.readings)
        device_state = readings['state'].lower()
        return task.action.lower() != device_state
    except KeyError:
        logger.error('Task - the device state cannot be obtained')
        return False
    except json.decoder.JSONDecodeError:
        logger.error('Task - the device readings cannot be converted to JSON')
        return False


def relay_action(device: Device, state: str):
    try:
        relay_factory = RelayFactory(device).obtain_factory()
        relay = relay_factory(None, device)
        action = relay.message(state)
        return action['state']
    except DeviceException as e:
        logger.error("Task -  problem to send message to the device - %s" % str(e))
    except KeyError:
        logger.error('Task - problem with message method state key not found')
    except Exception as e:
        logging.error('Task error - %s' % str(e))


def time_relay_task() -> list[str]:
    """
    At every minute check is any event to run
    :return:
    """
    tasks = DeviceEvent.objects.filter(type='time')
    # fired_tasks is for testing purposes
    fired_tasks = []
    for task in tasks:
        if not (is_event_time(task.time) and is_eligible_to_fire_task_based_on_readings(task)):
            continue
        # fire action
        action = relay_action(task.device, task.action)
        if action:
            fired_tasks.append(action)
    return fired_tasks


def get_sensor_reading_type(sensor: Device, reading_type: str) -> float or None:
    if not sensor or not sensor.readings:
        return None
    try:
        readings = json.loads(sensor.readings)
        return readings[reading_type]
    except KeyError:
        logger.error("Sensor task - reading type not found in sensor readings")
        return None
    except json.decoder.JSONDecodeError:
        logger.error("Sensor task - sensor readings cannot be converted")
        return None


def sensor_rule_task(rule: str, sensor_reading: float, task_reading: float) -> bool:
    try:
        rules = {
            '>': sensor_reading > task_reading,
            '<': sensor_reading < task_reading,
        }
        return rules[rule]
    except KeyError:
        logger.error("Sensor task - rule not found in sensor_rule_task")
        return False


def sensor_relay_task():
    """
    Every five minutes check sensor task based on sensor readings fire task
    :return:
    """
    tasks = DeviceEvent.objects.filter(type='sensor')
    # fired_tasks is for testing purposes
    fired_tasks = []
    for task in tasks:
        sensor = task.sensor
        sensor_reading = get_sensor_reading_type(sensor, task.reading_type)
        if sensor_reading and is_eligible_to_fire_task_based_on_readings(task) and sensor_rule_task(task.rule,
                                                                                                    sensor_reading,
                                                                                                    task.value):
            action = relay_action(task.device, task.action)
            if action:
                fired_tasks.append(action)
    return fired_tasks


@background
def task_for_every_hour():
    """
    At every hour save sensor reading to the database
    :return: None
    """
    sensor_periodic_tasks()


@background
def time_task():
    """
    Task runs for every minute
    :return:
    """
    time_relay_task()


@background
def senor_tasks():
    """
    Task runs for every five minutes
    :return:
    """
    sensor_relay_task()
