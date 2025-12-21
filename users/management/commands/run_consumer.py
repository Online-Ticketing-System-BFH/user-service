import asyncio
from django.core.management.base import BaseCommand
from users.messaging import start_consumer

class Command(BaseCommand):
    help = 'Starts the RabbitMQ consumer for booking confirmation events'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting RabbitMQ consumer...'))
        try:
            asyncio.run(start_consumer())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Consumer stopped'))
