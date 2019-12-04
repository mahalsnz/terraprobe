from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading
from skeleton.utils import get_current_season, calculate_reading_meter, calculate_irrigation_litres, calculate_irrigation_mms

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

#from .utils import

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from rain and meter'

    def handle(self, *args, **kwargs):
        logger.info('Running processrainmeter.....')
        logger.info('Check for rain and meter and null irrigation (litres).....')

        # TODO restrict to current season
        #season = get_current_season()
        #dates = 
        count = Reading.objects.filter(rain__isnull=False, meter__isnull=False, irrigation_litres__isnull=True).count()
        logger.info('We have ' + str(count) + ' readings to process')
        if count > 0:
            # TODO restrict to current season
            readings = Reading.objects.filter(rain__isnull=False, meter__isnull=False, irrigation_litres__isnull=True, type=1).order_by('-date')
            previous_date = None
            previous_meter = None
            for reading in readings:
                date = reading.date
                meter = reading.meter
                if previous_date:
                    logger.debug('Date:' + str(date) + ' PreviousDate:' + str(previous_date))
                    calculate_irrigation_litres()
                    calculate_irrigation_mms()
                else:
                    logger.debug('No previous date.')
                previous_date = date
                previous_meter = meter
        logger.info('Finished running processrainmeter.....')
