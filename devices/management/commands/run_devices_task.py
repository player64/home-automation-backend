from django.core.management.base import BaseCommand, CommandError

import logging

from devices.tasks import task_for_every_30_minutes

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Command to execute the background tasks'

    def handle(self, *args, **kwargs):
        try:
            thirty_minutes = 30*60
            task_for_every_30_minutes(repeat=thirty_minutes, repeat_until=None)
            print('Command executed')
        except:
            raise CommandError('Initialization failed.')
