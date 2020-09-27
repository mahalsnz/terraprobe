from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from graphs.models import vsw_reading
from django.db.models import Q

from skeleton.utils import get_current_season, get_site_season_start_end

import logging
import decimal

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

                top = 0 # Top of root zone is hard coded to zero
                bottom = getattr(site, rootzone + '_bottom')
                logger.debug("Top:" + str(top) + ' Bottom:' + str(bottom))
                if bottom is not None:
                #if top == 0 and bottom > 0:
                    seen_depth_in_bottom = False
                    first_no_depth = False
                    first_no_depth_value = 0
                    first_no_depth_he = 0
                    for i in range(1,11):
                        depths_key = {}
                        column = 'depth' + str(i)
                        depth = getattr(site, column)

                        if depth:
                            if depth > top and depth < bottom:
                                logger.debug(column + ' of site:' + str(depth))
                                he = int(getattr(site, 'depth_he' + str(i)))
                                depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom }
                                depth_array.append(depths_key)
                            if bottom == depth:
                                logger.debug(column + ' of site:' + str(depth))
                                logger.debug('Bottom equals a depth figure for this rootzone')
                                he = int(getattr(site, 'depth_he' + str(i)))
                                depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom  }
                                depth_array.append(depths_key)
                                seen_depth_in_bottom = True
                            if not seen_depth_in_bottom and depth > bottom:
                                logger.debug('Depth greater than Bottom and not seen_depth_in_bottom')
                                logger.debug(column + ' of site:' + str(depth))
                                he = int(getattr(site, 'depth_he' + str(i)))
                                depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom  }
                                depth_array.append(depths_key)
                                break
                        else:
                            logger.debug('No depth for column ' + column)
                            first_no_depth = True

                    # We have an exception here where we just add it to the depth_array
                    if not seen_depth_in_bottom:
                        depths_key = { 'depth' : bottom, 'he' : 0, 'rz_bottom' : bottom  }
                        depth_array.append(depths_key)
                rootzones[key] = depth_array
        logger.debug(rootzones)
        logger.info('Finished site root zone map.....')

        logger.info('Starting update of empty root zone readings for current season (all reading types).....')
        season = get_current_season()
        sites = Site.objects.filter().distinct()
        for site in sites:
            dates = get_site_season_start_end(site, season)

            # Using the vsw_readings view in the graph app as it has all the calibrations applied
            # Only get readings wher rz1 is null
            readings = vsw_reading.objects.filter(site_id=site.id, rz1__isnull=True, date__range=(dates.period_from, dates.period_to)).order_by('date')
            for reading in readings:
                # find rootzones in map for site and rz
                logger.debug("Reading Date: " + str(reading.date) + " Type: " + reading.type)
                for z in range(1,4):
                    rootzone = 'rz' + str(z)
                    key = str(reading.site_id) + rootzone
                    logger.debug("Key:" + key)
                    required_depths = rootzones[key]
                    logger.debug("Required Depths:" + str(required_depths))
                    total = 0
                    previous_vsw = 0
                    previous_he = 0
                    running_depth = 0
                    for depths_key in required_depths:
                        he = depths_key['he']
                        depth = depths_key['depth']
                        bottom = depths_key['rz_bottom']
                        logger.debug("Reading He:" + str(he) + ' Depth:' + str(depth) + ' preious he ' + str(previous_he))

                        # he can be zero if we are requiring a half for final reading
                        if he:
                            column = 'vsw' + str(he) + '_perc'

                            vsw = getattr(reading, column)

                            logger.debug("VSW reading for depth " + str(depth) + ' is ' + str(vsw))
                            if vsw:
                                # We no have some wierd rules. 1. If running depth is 0 and first depth is 20 add half of vsw to total
                                if depth == 20 and running_depth == 0:
                                    logger.debug("In running depth is 0 and first depth is 20")
                                    logger.debug("Adding " + str(vsw) + ' for interpoloated depth 10')
                                    total += vsw
                                #  2. If depth minus running depth equals 20 add together previous vsw with present vsw then divide by 2
                                elif (depth - running_depth) == 20:
                                    logger.debug("depth minus running depth equals 20")
                                    logger.debug("previous_vsw:" + str(previous_vsw) + "vsw:" + str(vsw))
                                    average = (previous_vsw + vsw) / 2
                                    logger.debug("Adding " + str(average) + ' for interpoloated depth ' + str(depth - 10))
                                    total += average
                                if depth <= bottom:
                                    logger.debug("Adding VSW " + str(vsw) + " for depth " + str(depth))
                                    total += vsw

                                #else:
                                #    # We half the depth figure that is above the Bottom. No? We should ignore a figure abover the bottom
                                #    half = vsw / 2
                                #    logger.debug("Adding half of VSW " + str(half) + " for depth " + str(depth) + ' as this depth is greater than bottom of ' + str(bottom))
                                #    total += half
                                previous_vsw = vsw
                                previous_he = he
                                running_depth = depth
                        '''
                        else:
                            logger.debug('In else ' + str(previous_he))
                            # We have the last interpolated value. We need the two previous values
                            column1 = 'vsw' + str(previous_he) + '_perc'
                            column2 = 'vsw' + str(previous_he - 1) + '_perc'
                            vsw1 = getattr(reading, column1)
                            vsw2 = getattr(reading, column2)

                            average = (vsw1 + vsw2) / 2
                            logger.debug("Adding " + str(average) + ' for interpoloated depth ' + str(depth))
                            total += average
                        '''
                    logger.info('Updating ' + rootzone + ' to ' + str(total) + ' for ' + site.name + ' on ' + str(reading.date) + ' for type ' + str(reading.type))

                    # Need to get a Reading object to update as we cannot update vsw_readings as it is a view
                    r = Reading.objects.get(site=reading.site_id, date=reading.date, type=reading.reading_type_id)

                    total = decimal.Decimal(total).quantize(decimal.Decimal('1'), rounding=decimal.ROUND_HALF_UP)
                    setattr(r, rootzone, total)
                    r.save() # Update
                # Finished looping through rootzones
            # Finished looping through readings
        # Finished looping through sites
        logger.info('Finished Update.....')
