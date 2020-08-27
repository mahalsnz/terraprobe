from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import Reading, Site, ETReading, KCReading, Product, Crop
from skeleton.utils import get_site_season_start_end, get_current_season, get_rz1_full_point_reading

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processes formulas to populate daily water use (EDWU)'

    def handle(self, *args, **kwargs):
        logger.info('Running processdailywateruse.....')

        # Get sites in current season that have readngs with a rz1 defined but no deficit
        season = get_current_season()
        sites = Site.objects.filter(readings__rz1__isnull=False, readings__deficit__isnull=True, readings__type__name='Probe').distinct()

        for site in sites:
            dates = get_site_season_start_end(site, season)

            readings = Reading.objects.filter(site=site.id, type=1, date__range=(dates.period_from, dates.period_to)).order_by('-date')

            # Get Full Point Reading for the Season
            rz1_full = get_rz1_full_point_reading(site, season)
            logger.info('Full Point RZ1 reading:' + str(rz1_full))

            # Get Crop Co-efficient (KC) for site
            #et = ETReading.objects.filter(state__localities__addresses__farm__site__id=site, )

            previous_date = None
            previous_reading = 0
            previous_deficit = 0
            for reading in readings:
                date = reading.date

                # Get Evapotranspiration (ET) for the site on the reading date
                et = ETReading.objects.get(state__localities__addresses__farm__site__id=site.id, date=date)
                daily_et = et.daily
                logger.debug('ET Reading:' + str(daily_et))
                daily_et = et.daily

                # Get Crop Co-efficient (KC) for site
                kc = KCReading.objects.get(period_from__lte=date, period_to__gte=date, crop__product__site__id=site.id)
                crop_kc = kc.kc
                logger.debug('KC Reading:' + str(crop_kc))

                # Get EDWU as et * kc
                edwu = round(daily_et * crop_kc, 2)
                logger.debug('EDWU:' + str(edwu))
                reading.estimated_dwu = edwu

                rz1 = reading.rz1
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
