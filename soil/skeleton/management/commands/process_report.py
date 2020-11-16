from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site

from skeleton.utils import get_current_season, get_site_season_start_end, get_rootzone_mapping

import logging
import decimal

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Pre process to report problem with data.'

    def handle(self, *args, **kwargs):
        logger.info('Running process_report.....')

        season = get_current_season()

        sites = Site.objects.filter(is_active=True, readings__rz1__isnull=True).distinct()
        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site_id=site.id, serial_number__isnull=True)

            # Readings have to have a serial number. Chnces are no serial number in reading means an onsite reading with no probe data
            for reading in readings:
                self.stdout.write('Site ' + str(site.site_number) + ':' + site.name + ' has a reading on ' + str(reading.date) + ' that appears to have no serial number\n')

        logger.info('Finished process_report.....')
