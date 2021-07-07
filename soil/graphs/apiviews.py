import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import vsw_reading, vsw_strategy
from skeleton.models import Farm, Site, Reading, SeasonStartEnd, SeasonalSoilStat, Document
from .serializers import VSWSerializer, VSWStrategySerializer, VSWDateSerializer
from django.db.models import Q, Sum
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from skeleton.utils import get_current_season, get_site_season_start_end, get_soil_type, calculate_seasonal_soil_stat
from django.db.models.functions import Coalesce

from django.core import management
import json, calendar

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWDateList(generics.ListAPIView):

    def get_queryset(self):

        queryset = SeasonStartEnd.objects.filter(site=self.kwargs["pk"], season_current_flag=True)

        return queryset
    serializer_class = VSWDateSerializer

class VSWDateListV2(generics.ListAPIView):

    def get_queryset(self):

        queryset = SeasonStartEnd.objects.filter(season=self.kwargs["season_id"], site=self.kwargs["site_id"])

        return queryset
    serializer_class = VSWDateSerializer

"""
    calculateStrategyPosition - Returns the Strategy Min and Max. Uses two strategys to get the interpolated min and max

    First calculate the strategy change per day:
    get the first strategy min point before the reading = 221.3 on October 5th
    get the first strategy min point after the reading = 245.5 on November 25th
    calculate the difference in the strategy (245.5 - 221.3 = 24.2mm)
    calculate the number of days between the strategy points (November 25th - October 5th = 31 days)
    calculate the strategy change per day (24.2mm / 31 days = 0.78mm per day)
    Then calculate the strategy on the reading date:
    calculate the days between the first strategy point before the reading and the reading (October 19th - October 5th = 14 days)
    determine the strategy change for that period (0.78mm per day x 14 days = 10.92mm)
    add this to the first strategy point before the reading (221.3 + 10.92 = 232.22mm on October 19th)
"""

def calculateStrategyPosition(after_strategy, before_strategy, latest_reading, full, refill):

    days_between_strategies = (after_strategy.strategy_date - before_strategy.strategy_date).days
    logger.debug('Days between strategies:' + str(days_between_strategies))

    # Calculation Upper
    diff = full.rz1 - refill.rz1
    before_upper = full.rz1 - ( diff - ( diff * before_strategy.percentage ))
    after_upper = full.rz1 - ( diff - ( diff * after_strategy.percentage ))
    logger.debug('Before Upper:' + str(before_upper) + ' After Upper:' + str(after_upper) )
    diff_upper = after_upper - before_upper
    logger.debug('Difference between Upper Strategies:' + str(diff_upper))

    if diff_upper == 0 or days_between_strategies == 0:
        day_change_upper = 0
    else:
        day_change_upper = diff_upper / days_between_strategies
    logger.debug('Day change for Upper:' + str(day_change_upper))

    # Calculation Lower
    before_lower = before_upper - ( diff * before_strategy.strategy_percentage )
    after_lower = after_upper - ( diff * before_strategy.strategy_percentage )
    logger.debug('Before Lower:' + str(before_lower) + ' After Lower:' + str(after_lower) )
    diff_lower = after_lower - before_lower
    logger.debug('Difference between Lower Strategies:' + str(diff_lower))
    if diff_upper == 0 or days_between_strategies == 0:
        day_change_lower = 0
    else:
        day_change_lower = diff_lower / days_between_strategies
    logger.debug('Day change for Lower:' + str(day_change_lower))

    # Days between the before strategy and the reading date
    days_between_before = (latest_reading.date - before_strategy.strategy_date).days
    logger.debug('days_between_before:' + str(days_between_before))
    upper_strategy_change = days_between_before * day_change_upper
    logger.debug('Upper Stategy Change:' + str(upper_strategy_change))
    lower_strategy_change = days_between_before * day_change_lower
    logger.debug('Lower Stategy Change:' + str(lower_strategy_change))

    # Add change to original before upper and before lower
    strategy_max = upper_strategy_change + before_upper
    strategy_min = lower_strategy_change + before_lower

    return strategy_max, strategy_min

"""
    calculateAlertLevel - Returns the alert level between 1 and 3 based on straegy min and max, and the latest reading rz1
"""

def calculateAlertLevel(strategy_max, strategy_min, latest_reading, full, refill):
    outside_limits = False
    outside_strategy = False
    if latest_reading.rz1 > full.rz1 or latest_reading.rz1 < refill.rz1:
        outside_limits = True
    if latest_reading.rz1 > strategy_max or latest_reading.rz1 < strategy_min:
        outside_strategy = True
    logger.debug('outside_limits:' + str(outside_limits) + ' outside_strategy:' + str(outside_strategy))

    alert_level = 0
    if outside_limits and outside_strategy:
        alert_level = 3
    elif outside_limits and not outside_strategy:
        alert_level = 2
    elif not outside_limits and outside_strategy:
        alert_level = 2
    else:
        alert_level = 1
    return alert_level

class FruitionSummaryV2(APIView):
    def get(self, request, site_ids, format=None):
        ids = request.GET.getlist('sites[]')
        season = get_current_season()
        strategy_serialized_data = []
        for site_id in ids:
            try:
                site = Site.objects.get(pk=site_id)
                dates = get_site_season_start_end(site, season)
                latest_reading = vsw_reading.objects.filter(site=site.id, date__range=(dates.period_from, dates.period_to), type='Probe', reviewed=True).latest('date')
                full = vsw_reading.objects.get(site_id=site_id, type='Full Point', date__range=(dates.period_from, dates.period_to))
                refill = vsw_reading.objects.get(site_id=site_id, type='Refill', date__range=(dates.period_from, dates.period_to))

                after_strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__gte=latest_reading.date)).order_by('strategy_date')[0]
                before_strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__lte=latest_reading.date)).order_by('-strategy_date')[0]

                strategy_max, strategy_min = calculateStrategyPosition(after_strategy, before_strategy, latest_reading, full, refill)
                alert_level = calculateAlertLevel(strategy_max, strategy_min, latest_reading, full, refill)
                reading_serializer = VSWSerializer(latest_reading)
                before_strategy_serializer = VSWStrategySerializer(before_strategy)
                after_strategy_serializer = VSWStrategySerializer(after_strategy)

                strategy_serialized_data.append({
                    'site_id': site.id,
                    'latest_reading_date': latest_reading.date,
                    'latest_reading_date_rz1': latest_reading.rz1,
                    'full_point': full.rz1,
                    'refill_point': refill.rz1,
                    'strategy_max' : round(strategy_max, 2),
                    'strategy_min' : round(strategy_min, 2),
                    'alert_level' : alert_level,
                    'latest_reading': reading_serializer.data,
                    'closest_strategies' : [before_strategy_serializer.data, after_strategy_serializer.data]
                })

            except ObjectDoesNotExist:
                pass # No latest reading
            except IndexError:
                pass # No strategy

        data = {
            'sites': strategy_serialized_data,
        }

        return Response(data)

class FruitionSummary(APIView):

    def get(self, request, site_ids, format=None):
        logger.debug(str(request.GET))
        ids = request.GET.getlist('sites[]')
        logger.debug(ids)
        season = get_current_season()
        strategy_serialized_data = []
        for site_id in ids:
            try:
                site = Site.objects.get(pk=site_id)
                # Get sites full point and refill readings for season
                dates = get_site_season_start_end(site, season)
                latest_reading = vsw_reading.objects.filter(site=site.id, date__range=(dates.period_from, dates.period_to), type='Probe', reviewed=True).latest('date')
                logger.debug('Latest Date for site :' + str(site.name) + ' - ' + str(latest_reading.date) + ' RZ1:' + str(latest_reading.rz1))

                full = vsw_reading.objects.get(site_id=site_id, type='Full Point', date__range=(dates.period_from, dates.period_to))
                refill = vsw_reading.objects.get(site_id=site_id, type='Refill', date__range=(dates.period_from, dates.period_to))
                logger.debug('Full Point rz1:' + str(full.rz1) + ' Refill rz1:' + str(refill.rz1))

                # get the strategy on either side of the latest reading date
                after_strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__gte=latest_reading.date)).order_by('strategy_date')[0]
                logger.debug('After Strategy:' + str(after_strategy.strategy_date) + ' percentage ' + str(after_strategy.percentage) )
                before_strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__lte=latest_reading.date)).order_by('-strategy_date')[0]
                logger.debug('Before Strategy:' + str(before_strategy.strategy_date) + ' percentage ' + str(before_strategy.percentage) )

                # Get the days between before and after
                days_between_strategies = (after_strategy.strategy_date - before_strategy.strategy_date).days
                logger.debug('Days between strategies:' + str(days_between_strategies))

                # Calculation
                diff = full.rz1 - refill.rz1
                before_upper = full.rz1 - ( diff - ( diff * before_strategy.percentage ))
                after_upper = full.rz1 - ( diff - ( diff * after_strategy.percentage ))
                logger.debug('Before Upper:' + str(before_upper) + ' After Upper:' + str(after_upper) )
                diff_upper = after_upper - before_upper
                logger.debug('Difference between Upper Strategies:' + str(diff_upper))
                if diff_upper == 0 or days_between_strategies == 0:
                    day_change_upper = 0
                else:
                    day_change_upper = diff_upper / days_between_strategies
                logger.debug('Day change for Upper:' + str(day_change_upper))

                before_lower = before_upper - ( diff * before_strategy.strategy_percentage )
                after_lower = after_upper - ( diff * before_strategy.strategy_percentage )
                logger.debug('Before Lower:' + str(before_lower) + ' After Lower:' + str(after_lower) )
                diff_lower = after_lower - before_lower
                logger.debug('Difference between Lower Strategies:' + str(diff_lower))
                if diff_upper == 0 or days_between_strategies == 0:
                    day_change_lower = 0
                else:
                    day_change_lower = diff_lower / days_between_strategies
                logger.debug('Day change for Lower:' + str(day_change_lower))

                # Days between the before strategy and the reading date
                days_between_before = (latest_reading.date - before_strategy.strategy_date).days
                logger.debug('days_between_before:' + str(days_between_before))
                upper_strategy_change = days_between_before * day_change_upper
                logger.debug('Upper Stategy Change:' + str(upper_strategy_change))
                lower_strategy_change = days_between_before * day_change_lower
                logger.debug('Lower Stategy Change:' + str(lower_strategy_change))

                # Add change to original before upper and before lower
                strategy_max = upper_strategy_change + before_upper
                strategy_min = lower_strategy_change + before_lower

                outside_limits = False
                outside_strategy = False
                if latest_reading.rz1 > full.rz1 or latest_reading.rz1 < refill.rz1:
                    outside_limits = True
                if latest_reading.rz1 > strategy_max or latest_reading.rz1 < strategy_min:
                    outside_strategy = True
                logger.debug('outside_limits:' + str(outside_limits) + ' outside_strategy:' + str(outside_strategy))

                alert_level = 0
                if outside_limits and outside_strategy:
                    alert_level = 3
                elif outside_limits and not outside_strategy:
                    alert_level = 2
                elif not outside_limits and outside_strategy:
                    alert_level = 2
                else:
                    alert_level = 1

                strategy_serialized_data.append({
                    'site_id': site.id,
                    'latest_reading_date': latest_reading.date,
                    'latest_reading_date_rz1': latest_reading.rz1,
                    'strategy_date': before_strategy.strategy_date,
                    'full_point': full.rz1,
                    'refill_point': refill.rz1,
                    'strategy_max' : round(strategy_max, 2),
                    'strategy_min' : round(strategy_min, 2),
                    'alert_level' : alert_level
                })

            except ObjectDoesNotExist:
                pass # No latest reading
            except IndexError:
                pass # No strategy

        data = {
            'sites': strategy_serialized_data,
        }

        return Response(data)

#TODO: Not the best way to do the ready-reviwed option for getting readings.
class VSWReadingList(generics.ListAPIView):

    def get_queryset(self):
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_reading.objects.filter(site_id=self.kwargs["pk"], date__range=(self.kwargs["period_from"], self.kwargs["period_to"]) )

        return queryset
    serializer_class = VSWSerializer

class VSWReadingReadyList(generics.ListAPIView):

    def get_queryset(self):
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_reading.objects.filter(site_id=self.kwargs["pk"], date__range=(self.kwargs["period_from"], self.kwargs["period_to"]), reviewed=self.kwargs["reviewed"] )

        return queryset
    serializer_class = VSWSerializer

class VSWStrategyList(generics.ListAPIView):

    def get_queryset(self):
        queryset = vsw_strategy.objects.filter(site_id=self.kwargs["pk"], reading_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]), critical_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWStrategySerializer

class EOYFarmSummary(APIView):

    def get(self, request, farm_id, season_id, template_id, format=None):

        # Checks each season and calculates stats if not there
        calculate_seasonal_soil_stat()

        farms = Farm.objects.select_related('weatherstation').filter(id=farm_id)
        template = Document.objects.get(pk=template_id)
        template_data = template.document.read() # Store template as we are going to return it as part of API data

        # Test Data with prod switch for testing
        rain_json = [{
                    "Oct": 76
                },
                {
                    "Nov": 524
                },
                {
                    "Dec": 19
                },
                {
                    "Jan": 21
                },
                {
                    "Feb": 132
                },
                {
                    "Mar": 44
                },
                {
                    "Apr": 1
                },
                {
                    "May": 13
                },
                {
                    "Jun": 3
                }]
        ten_year_average_rainfall = 0

        eoy_data = []
        for farm in farms:

            prod = True
            if prod == True:
                rain_data = management.call_command('request_to_hortplus', purpose='generate_eoy_data', stations=farm.weatherstation.code)
                rain_data = json.loads(rain_data)
                logger.debug('Rain data:' + str(rain_data))

                rain_json = []
                for month in rain_data:
                    if (rain_data[month]['avg'] > 0):
                        ten_year_average_rainfall += rain_data[month]['avg']
                        d = round(rain_data[month]['cur'] / (rain_data[month]['avg'] / 10) * 100)
                        int_month = int(month)
                        rain_json.append({ calendar.month_abbr[int_month]: d })
                        logger.debug(rain_json)
                ten_year_average_rainfall = ten_year_average_rainfall / 10 # Average is total for 10 years

            # Get only active sites
            sites = Site.objects.select_related('product__crop').select_related('product__variety').filter(is_active=True, farm=farm)

            for site in sites:
                season = SeasonStartEnd.objects.get(site_id=site.id, season_id=season_id) # get season
                logger.debug('Season: ' + str(season.season_name) + ' Farm:' + str(farm.name) + ' Weatherstation ' + farm.weatherstation.name +
                    ' Site:' + str(site.site_number))

                last_season = SeasonStartEnd.objects.filter(site_id=site.id).order_by('-period_from') # get last season
                last_season_irrigation_mms_sum = 0
                try:
                    last_season = last_season[1]
                    last_season_readings = Reading.objects.filter(site=site.id, type__name="Probe", date__range=(last_season.period_from, last_season.period_to))
                    last_season_irrigation_mms = last_season_readings.aggregate(last_season_irrigation_mms__sum=Coalesce(Sum('irrigation_mms'), 0))
                    last_season_irrigation_mms_sum = last_season_irrigation_mms.get('last_season_irrigation_mms__sum')
                except IndexError:
                    pass

                rain_sum = 0
                irrigation_mms_diff = 0.0
                irrigation_mms_perc = 0.0

                eff_irrigation_diff = 0.0
                eff_irrigation_perc = 0.0
                average_eff_irrigation_diff = 0.0

                readings = Reading.objects.filter(site=site.id, type__name="Probe", date__range=(season.period_from, season.period_to))
                full_point = Reading.objects.get(site=site.id, type__name="Full Point", date__range=(season.period_from, season.period_to))

                soil_type = get_soil_type(full_point.rz1)
                stats = SeasonalSoilStat.objects.get(season=season.season, crop=site.product.crop, soil_type=soil_type)
                average_eff_irrigation = stats.total_effective_irrigation
                average_eff_irrigation_perc = stats.perc_effective_irrigation
                soil_type = stats.get_soil_type_display()
                logger.debug('Average_eff_irrigation_perc for all sites of soil type:' + soil_type + ' is ' + str(average_eff_irrigation_perc))

                rainfall = readings.aggregate(rain__sum=Coalesce(Sum('rain'), 0))
                rain_sum = rainfall.get('rain__sum')

                irrigation_mms = readings.aggregate(irrigation_mms__sum=Coalesce(Sum('irrigation_mms'), 0))
                irrigation_mms_sum = irrigation_mms.get('irrigation_mms__sum')

                eff_irrigation = readings.aggregate(effective_irrigation__sum=Coalesce(Sum('effective_irrigation'), 0))
                eff_irrigation_sum = eff_irrigation.get('effective_irrigation__sum')

                try:
                    eff_irrigation_perc = round(eff_irrigation_sum / irrigation_mms_sum * 100)
                except ZeroDivisionError:
                    eff_irrigation_perc = 0
                logger.debug('Effective Irrigation %:' + str(eff_irrigation_perc))

                average_eff_irrigation_diff = average_eff_irrigation_perc - eff_irrigation_perc

                logger.debug('Rainfall Sum:' + str(rain_sum))

                eoy_data.append({
                    'site' : site.name,
                    'site_id' : site.id,
                    'site_number' : site.site_number,
                    'period_from' : season.period_from,
                    'period_to' : season.period_to,
                    'soil_type' : soil_type,
                    'product' : site.product.crop.name + ' - ' + site.product.variety.name,
                    'rz1' : site.rz1_bottom,
                    'application_rate' : site.application_rate,
                    'rain': rain_sum,
                    'irrigation_mms': irrigation_mms_sum,
                    'last_season_irrigation_mms': last_season_irrigation_mms_sum,
                    'irrigation_mms_perc': irrigation_mms_perc,
                    'eff_irrigation' : eff_irrigation_sum,
                    'eff_irrigation_perc' : eff_irrigation_perc,
                    'average_eff_irrigation' : average_eff_irrigation,
                    'average_eff_irrigation_perc' : average_eff_irrigation_perc
                })


        data = {
            "farm": farm.name,
            'season': season.season_name,
            'weatherstation': farm.weatherstation.name,
            'ten_year_average_rainfall': ten_year_average_rainfall,
            'template': template_data,
            'site_data': eoy_data,
            'rain_data': rain_json
        }

        return Response(data)
