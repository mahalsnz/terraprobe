from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from skeleton.utils import get_site_season_start_end, get_current_season

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from meter'

    def handle(self, *args, **kwargs):
        logger.info('Running processmeter.....')
        logger.info('Check for meter and null irrigation (litres).....')

        # Get sites in current season that have readngs with a meter reading but no irrigation in litres
        season = get_current_season()
        sites = Site.objects.filter(readings__meter__isnull=False, readings__irrigation_litres__isnull=True, readings__type=1).distinct()

        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')
            previous_date = None
            previous_meter = None
            previous_reading = None
            for reading in readings:
                date = reading.date
                meter = reading.meter
                if previous_date:
                    logger.debug('Date:' + str(date) + ' PreviousDate:' + str(previous_date))

                    irrigation_litres = round((previous_meter - meter) / site.irrigation_position, 2)
                    logger.debug('I litres:' + str(irrigation_litres))

                    irrigation_mms = round(irrigation_litres / ((site.row_spacing * site.plant_spacing) / 10000), 2)
                    logger.debug('I mms:' + str(irrigation_mms))

                    previous_reading.irrigation_litres = irrigation_litres
                    previous_reading.irrigation_mms = irrigation_mms
                    previous_reading.save()
                else:
                    logger.debug('No previous date.')
                previous_date = date
                previous_meter = meter
                previous_reading = reading
        logger.info('Finished running processmeter.....')
