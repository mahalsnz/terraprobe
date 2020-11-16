from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site, ETReading, KCReading, Product, Crop
from skeleton.utils import get_site_season_start_end, get_current_season, get_rz1_full_point_reading, SiteReadingException

import decimal
import logging
import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate daily water use (EDWU)'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--sites', type=open, help='A list of sites to populate daily water use for.')


    def handle(self, *args, **kwargs):
        logger.info('Running processdailywateruse.....')

        # Get sites in current season that have readngs with a rz1 defined but no deficit
        season = get_current_season()

        if kwargs['sites']:
            sites = kwargs['sites']
            logger.info('Starting update of daily water use readings for sites that have just been uploaded.' + str(sites))
        else:
            sites = Site.objects.filter(is_active=True, readings__rz1__isnull=False, readings__deficit__isnull=True, readings__type__name='Probe').distinct()
            logger.info('Starting update of daily water use readings for all sites that have a reading deficit of null.' + str(sites))

        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')

            # Get Full Point Reading for the Season
            rz1_full = get_rz1_full_point_reading(site, season)
            logger.info('Full Point RZ1 reading:' + str(rz1_full))

            previous_date = None
            previous_reading = 0
            previous_deficit = 0
            for reading in readings:
                logger.debug(str(reading))
                date = reading.date

                logger.debug('Getting RT and KC readings for date: ' + str(date))
                month = date.strftime("%m")
                day = date.strftime("%d")

                logger.debug('Ignoring year and getting month:day' + str(month) + ':' + str(day))

                # Get Evapotranspiration (ET) for the site on the reading date. Ignore year as this data is by day and is the same every season
                try:
                    et = ETReading.objects.get(date__month=month, date__day=day)
                except:
                    raise SiteReadingException("No ET reading found for " + str(date), site)
                daily_et = round(et.daily, 2)
                logger.debug('ET Reading:' + str(daily_et))

                # Get Crop Co-efficient (KC) for site. Need to get it between periods
                try:
                    kc = KCReading.objects.get(period_from__lte=date, period_to__gte=date, crop__product__site__id=site.id)
                except:
                    raise SiteReadingException("No KC reading found for " + str(date), site)

                crop_kc = round(kc.kc, 2)
                logger.debug('KC Reading:' + str(crop_kc))

                # Get EDWU as et * kc
                edwu = daily_et * crop_kc
                edwu = round(edwu, 2)
                logger.debug('EDWU:' + str(edwu))
                reading.estimated_dwu = edwu

                rz1 = reading.rz1
                if rz1 == None:
                    raise SiteReadingException("Root Zone 1 is blank for reading date " + str(date), site)
                deficit = round(rz1_full - rz1, 2)
                logger.debug('Deficit:' + str(deficit))
                reading.deficit = deficit

                if previous_date:
                    logger.debug('Date:' + str(date) + ' PreviousDate:' + str(previous_date))

                    # Find the amount of days between
                    days = previous_date - date
                    logger.debug('Days:' + str(days.days))
                    pdwu = round((previous_deficit - deficit) / days.days, 2)
                    logger.debug('PDWU:' + str(pdwu))
                    previous_reading.probe_dwu = pdwu
                    previous_reading.save()
                else:
                    logger.debug('No previous date.')
                previous_date = date
                previous_deficit = deficit
                previous_reading = reading
                reading.save()

        logger.info('Finished processdailywateruse.....')
