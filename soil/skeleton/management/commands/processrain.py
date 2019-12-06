from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from skeleton.utils import get_site_season_start_end, get_current_season, get_rz1_full_point_reading

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from rain (runs last)'

    def handle(self, *args, **kwargs):
        logger.info('Running processrain.....')
        logger.info('Check for meter and null irrigation (litres).....')

        # Get sites in current season that have readngs with a rain reading but no effective_rain_1
        season = get_current_season()
        sites = Site.objects.filter(readings__meter__isnull=False, readings__effective_rain_1__isnull=True, readings__type=1).distinct()

        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')

            # Get Full Point Reading for the Season
            rz1_full = get_rz1_full_point_reading(site, season)
            logger.info('Full Point RZ1 reading:' + str(rz1_full))

            previous_date = None
            previous_rz1 = None
            previous_reading = None
            previous_edwu = None
            previous_rain = None
            for reading in readings:
                date = reading.date
                rz1 = reading.rz1
                edwu = reading.estimated_dwu
                rain = reading.rain
                if previous_date:
                    effrain1 = 0
                    effectiverainfall = 0
                    logger.debug('Date:' + str(date) + ' RZ1:' + str(rz1) + ' PreviousDate:' + str(previous_date) + ' RZ1 ' + str(previous_rz1))

                    diff = previous_rz1 - rz1
                    logger.debug('Diff between Now and Previous:' + str(diff))
                    rz1_diff = previous_rz1 - diff
                    logger.debug('RZ1-Diff:' + str(rz1_diff))

                    edwu_factor = previous_edwu * 3
                    logger.debug('EDWU Factor:' + str(edwu_factor))

                    logger.debug('Rain:' + str(previous_rain))

                    sub_total = rz1_diff - edwu_factor + previous_rain
                    logger.debug('RZ1-Diff - EDWU Factor + Rain=' + str(sub_total))

                    # Compare sub_total to full point reading
                    if rz1_full >= sub_total:
                        effrain1 = round(previous_rain - 5, 2)
                    else:
                        effrain1 = round(rz1_full - (rz1_diff + edwu_factor), 2)
                    logger.debug('Effrain1:' + str(effrain1))

                    previous_reading.effrain1 = effrain1

                    if effrain1 > 0:
                        effectiverainfall = effrain1

                    logger.debug('Effective Rainfall:' + str(effectiverainfall))
                    previous_reading.effectiverainfall = effectiverainfall

                    previous_reading.save()
                else:
                    logger.debug('No previous date.')

                previous_date = date
                previous_rz1 = rz1
                previous_edwu = edwu
                previous_rain = rain
                previous_reading = reading
                reading.save()

        logger.info('Finishing processrain.....')
