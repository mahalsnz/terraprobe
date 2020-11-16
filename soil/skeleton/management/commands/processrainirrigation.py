from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site
from skeleton.utils import get_site_season_start_end, get_current_season, get_rz1_full_point_reading

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate reading fields derived from rain (runs last)'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--sites', type=open, help='A list of sites to process rain and irrigation for.')

    def handle(self, *args, **kwargs):
        logger.info('Running processrainirrigation.....')

        season = get_current_season()

        if kwargs['sites']:
            sites = kwargs['sites']
            logger.info('Starting update of rain and irrigation readings for sites that have just been uploaded.' + str(sites))
        else:
            sites = Site.objects.filter(is_active=True, readings__effective_irrigation__isnull=True, readings__type__name='Probe').distinct()
            logger.info('Starting update of rain and irrigation readings for all sites that have a null effective irrigation.' + str(sites))

        for site in sites:
            dates = get_site_season_start_end(site, season)

            # Get Full Point Reading for the Season
            rz1_full = get_rz1_full_point_reading(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')
            previous_date = None
            previous_rz1 = 0
            previous_reading = None
            previous_edwu = 0
            previous_rain = 0
            previous_irrigation_mms = 0

            for reading in readings:
                if reading.serial_number is None:
                    raise SiteReadingException("No serial number found for reading date " + str(date), site)

                date = reading.date
                rz1 = reading.rz1
                edwu = reading.estimated_dwu
                rain = reading.rain
                irrigation_mms = reading.irrigation_mms

                if irrigation_mms is None:
                    irrigation_mms = 0

                if previous_date:
                    effrain1 = 0
                    effectiverainfall = 0
                    logger.debug('Date:' + str(date) + ' RZ1:' + str(rz1) + ' PreviousDate:' + str(previous_date) + ' RZ1 ' + str(previous_rz1))

                    diff = previous_rz1 - rz1
                    logger.debug('Diff between Now and Previous:' + str(diff))
                    rz1_diff = previous_rz1 - diff
                    logger.debug('RZ1-Diff:' + str(rz1_diff))

                    edwu_factor3 = previous_edwu * 3
                    logger.debug('EDWU Factor for Rain (*3):' + str(edwu_factor3))
                    edwu_factor5 = previous_edwu * 5
                    logger.debug('EDWU Factor for Irrigation (*5):' + str(edwu_factor5))

                    logger.debug('Rain:' + str(previous_rain))

                    sub_total_rain = rz1_diff - edwu_factor3 + previous_rain
                    logger.debug('RZ1-Diff - EDWU Factor 3 + Rain =' + str(sub_total_rain))

                    sub_total_irrigation = 0
                    logger.debug('irrigation_mms:' + str(previous_irrigation_mms))
                    if irrigation_mms > 0:
                        sub_total_irrigation = rz1_diff - edwu_factor5 + (previous_irrigation_mms / 4)
                    logger.debug('RZ1-Diff - EDWU Factor 5 + (Irrigation mms / 4) =' + str(sub_total_irrigation))

                    # Compare sub_total_rain to full point reading
                    if rz1_full >= sub_total_rain:
                        effrain1 = round(previous_rain - 5, 2)
                    else:
                        effrain1 = round(rz1_full - (rz1_diff + edwu_factor3), 2)
                    logger.debug('Effrain1 for date ' + str(previous_date) + ':' + str(effrain1))

                    if effrain1 > 0:
                        effectiverainfall = effrain1

                    logger.debug('Effective Rainfall for date ' + str(previous_date) + ':' + str(effectiverainfall))

                    # # Compare sub_total_irrigation to full point reading
                    if rz1_full >= sub_total_irrigation:
                        efflrr1 = previous_irrigation_mms
                    else:
                        efflrr1 = round(rz1_full - (rz1_diff + edwu_factor5), 2)

                    if efflrr1 > 0:
                        efflrr2 = efflrr1
                    else:
                        efflrr2 = 0

                    effective_irrigation = 0
                    if previous_irrigation_mms > 0:
                        effective_irrigation = efflrr2
                    logger.debug('Effective Irrigation for date ' + str(previous_date) + ':' + str(effective_irrigation))

                    previous_reading.effective_rain_1 = effrain1
                    previous_reading.effective_rainfall = effectiverainfall
                    previous_reading.effective_irrigation = effective_irrigation
                    previous_reading.save()
                else:
                    logger.debug('No previous date.')
                previous_date = date
                previous_rz1 = rz1
                previous_edwu = edwu
                previous_rain = rain
                previous_reading = reading
                previous_irrigation_mms = irrigation_mms

            logger.debug('End loop of readings for a site')
        logger.info('Finishing processrain.....')
