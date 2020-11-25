import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import vsw_reading, vsw_strategy
from skeleton.models import Farm, Site, SeasonStartEnd
from .serializers import VSWSerializer, SiteSerializer, FarmSerializer, ReadingTypeSerializer, VSWStrategySerializer, VSWDateSerializer
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWDateList(generics.ListAPIView):

    def get_queryset(self):

        queryset = SeasonStartEnd.objects.filter(site=self.kwargs["pk"], season_current_flag=True)

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
        queryset = vsw_reading.objects.filter(site=self.kwargs["pk"], date__range=(self.kwargs["period_from"], self.kwargs["period_to"]) )

        return queryset
    serializer_class = VSWSerializer

class VSWReadingReadyList(generics.ListAPIView):

    def get_queryset(self):
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_reading.objects.filter(site=self.kwargs["pk"], date__range=(self.kwargs["period_from"], self.kwargs["period_to"]), reviewed=self.kwargs["reviewed"] )

        return queryset
    serializer_class = VSWSerializer

class VSWStrategyList(generics.ListAPIView):

    def get_queryset(self):
        queryset = vsw_strategy.objects.filter(site=self.kwargs["pk"], reading_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]), critical_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWStrategySerializer
