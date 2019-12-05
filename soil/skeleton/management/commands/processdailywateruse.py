from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from skeleton.utils import get_site_season_start_end, get_current_season

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate daily water use (EDWU)'

    def handle(self, *args, **kwargs):
        logger.info('Running processdailywateruse.....')

        # Get sites in current season that have readngs with a rz1 defined but no deficit
        season = get_current_season()
        sites = Site.objects.filter(readings__rz1__isnull=False, readings__deficit__isnull=True, readings__type=1).distinct()

        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')
            reading_full = Reading.objects.get(site=site.id, type=2, date__range=(dates.period_from, dates.period_to))
            rz1_full = reading_full.rz1
            logger.info('Full Point RZ1 reading:' + str(rz1_full))

            previous_date = None
            previous_reading = None
            previous_deficit = None
            for reading in readings:
                date = reading.date
                rz1 = reading.rz1
                deficit = round(rz1_full - rz1, 2)
                logger.debug('Deficit:' + str(deficit))
                if previous_date:
                    logger.debug('Date:' + str(date) + ' PreviousDate:' + str(previous_date))

                    pdwu = round(7 / (previous_deficit - deficit), 2)
                    logger.debug('pdwu:' + str(pdwu))

                else:
                    logger.debug('No previous date.')
                previous_date = date
                previous_deficit = deficit
                previous_reading = reading


        logger.info('Finished processdailywateruse.....')
