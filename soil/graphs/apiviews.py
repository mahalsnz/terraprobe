import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

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

                strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__gte=latest_reading.date)).order_by('strategy_date')[0]
                logger.debug('Strategy:' + str(strategy.strategy_date) + ' percentage ' + str(strategy.percentage) )

                # Calculation
                diff = full.rz1 - refill.rz1
                upper = full.rz1 - ( diff - ( diff * strategy.percentage ))
                lower = upper - ( diff * strategy.strategy_percentage )

                logger.debug('Upper:' + str(upper) + ' Lower:' + str(lower))

                strategy_serialized_data.append({
                    'site_id': site.id,
                    'latest_reading_date': latest_reading.date,
                    'latest_reading_date_rz1': latest_reading.rz1,
                    'strategy_date': strategy.strategy_date,
                    'full_point': full.rz1,
                    'refill_point': refill.rz1,
                    'strategy_max' : round(upper, 1),
                    'strategy_min' : round(lower, 1)
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
