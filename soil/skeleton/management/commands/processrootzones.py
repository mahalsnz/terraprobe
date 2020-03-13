from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from graphs.models import vsw_reading
from django.db.models import Q

from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from rain and meter'

    def handle(self, *args, **kwargs):
        logger.info('Running processrootzones.....')

        logger.info('Creating site root zone map.....')
        # TODO Restrict this to active sites
        sites = Site.objects.all()
        rootzones = {}
        for site in sites:
            logger.info('Processing Site ' + site.name)
            for z in range(1,4):
                rootzone = 'rz' + str(z)
                key = str(site.id) + rootzone
                logger.debug("Key:" + key)
                depth_array = []
                rootzones[key] = []

                top = getattr(site, rootzone + '_top')
                bottom = getattr(site, rootzone + '_bottom')
                logger.debug("Top:" + str(top) + ' Bottom:' + str(bottom))
                if top != None and bottom != None:
                    for i in range(1,11):
                        column = 'depth' + str(i)
                        depth = getattr(site, column)
                        logger.debug(column + ' of site:' + str(depth))
                        if depth:
                            if depth > top and depth < bottom:
                                he = int(getattr(site, 'depth_he' + str(i)))
                                depth_array.append(he)
                        else:
                            logger.debug('No depth')
                rootzones[key] = depth_array
        logger.debug(rootzones)
        logger.info('Finished site root zone map.....')

        logger.info('Starting update of empty root zone readings for current season (all reading types).....')
        season = get_current_season()
        sites = Site.objects.filter(Q(readings__rz1__isnull=True)|Q(readings__rz2__isnull=True)|Q(readings__rz3__isnull=True),).distinct()
        for site in sites:
            dates = get_site_season_start_end(site, season)

            # Using the vsw_readings view in the graph app as it has all the calibrations applied
            readings = vsw_reading.objects.filter(site_id=site.id, date__range=(dates.period_from, dates.period_to)).order_by('date')

            for reading in readings:
                # find rootzones in map for site and rz
                for z in range(1,4):
                    rootzone = 'rz' + str(z)
                    key = str(reading.site_id) + rootzone
                    logger.debug("Key:" + key)
                    required_depths = rootzones[key]
                    logger.debug("Required Depths:" + str(required_depths))
                    total = 0
                    for depth in required_depths:
                        column = 'vsw' + str(depth) + '_perc'
                        vsw = getattr(reading, column)

                        logger.debug("VSW reading for depth " + str(depth) + ' is ' + str(vsw))
                        if vsw:
                            total += vsw

                    logger.info('Updating ' + rootzone + ' to ' + str(total) + ' for ' + site.name + ' on ' + str(reading.date))

                    # Need to get a Reading object to update as we cannot update vsw_readings as it is a view
                    r = Reading.objects.get(site=reading.site_id, date=reading.date)
                    setattr(r, rootzone, total)
                    r.save() # Update
                # Finished looping through rootzones
            # Finished looping through readings
        # Finished looping through sites
        logger.info('Finished Update.....')
