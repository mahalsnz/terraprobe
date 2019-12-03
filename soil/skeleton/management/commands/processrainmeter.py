from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading
from skeleton.utils import calculate_reading_meter, calculate_irrigation_litres, calculate_irrigation_mms

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

#from .utils import

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from rain and meter'

    def handle(self, *args, **kwargs):
        logger.info('Running process_rain_meter.....')
        logger.info('Check for rain and meter and null irrigation (litres).....')
        count = Reading.objects.filter(rain__isnull=False, meter__isnull=False, irrigation_litres__isnull=True).count()
        logger.info('We have ' + str(count) + ' readings to process')
        if count > 0:
            readings = Reading.objects.filter(rain__isnull=False, meter__isnull=False, irrigation_litres__isnull=True, type=1).order_by('-date')
            for reading in readings:
                logger.info('reading.depth1' + str(reading.depth1))
                calculate_irrigation_litres()
                calculate_irrigation_mms()
        logger.info('Finished running process_rain_meter.....')
