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

        # Get sites in current season that have readngs with at least one meter reading but no irrigation in litres
        season = get_current_season()
        sites = Site.objects.filter(is_active=True, readings__meter__isnull=False, readings__irrigation_litres__isnull=True, readings__type__name='Probe').distinct()
        logger.info('Sites' + str(sites))
        for site in sites:
            logger.info('Processing Site ' + site.name)
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')
            previous_date = None
            previous_meter = None
            previous_reading = None
            for reading in readings:
                date = reading.date
                meter = reading.meter
                if previous_date and meter:
                    logger.debug('Date:' + str(date) + ' meter:' + str(meter) + ' PreviousDate:' + str(previous_date) + ' previous meter:' + str(previous_meter))

                    # When it comes to processing the meter reading, if the difference between last week and this week is less than one,
                    # the system will realise that this is a faulty meter and data cannot be derived between the reset and previous meter reading.
                    # This will cause zero's for the derived fields that depend on this for that weeks reading.
                    if meter > previous_meter:
                        irrigation_litres = 0
                        irrigation_mms = 0

                    else:
                        irrigation_litres = round((previous_meter - meter) / site.irrigation_position, 2)
                        irrigation_mms = round(irrigation_litres / ((site.row_spacing * site.plant_spacing * 10000) / 10000), 2)

                    logger.debug('Irrigation litres:' + str(irrigation_litres))
                    logger.debug('Irrigation mms:' + str(irrigation_mms))
                    previous_reading.irrigation_litres = irrigation_litres
                    previous_reading.irrigation_mms = irrigation_mms
                    logger.debug('Previous Reading:' + str(previous_reading))
                    previous_reading.save()
                else:
                    logger.debug('No previous date for reading date:' + str(date))
                    if meter == None:
                        # Alert but don't stop for No Meter Reading
                        self.stdout.write('No meter reading for latest reading date ' + str(date) + ' for site ' + site.name + '\n')
                        continue
                previous_date = date
                previous_meter = meter
                previous_reading = reading
        logger.info('Finished running processmeter.....')
