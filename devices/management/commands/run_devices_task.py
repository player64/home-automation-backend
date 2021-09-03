from django.core.management.base import BaseCommand, CommandError

import logging

from devices.tasks import task_for_every_hour

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Command to execute the background tasks'

    def handle(self, *args, **kwargs):
        try:
            one_hour = 60*60
            task_for_every_hour(repeat=one_hour, repeat_until=None)
            print('Command executed')
        except:
            raise CommandError('Initialization failed.')
