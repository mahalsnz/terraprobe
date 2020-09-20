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

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWDateList(generics.ListAPIView):

    def get_queryset(self):

        queryset = SeasonStartEnd.objects.filter(site=self.kwargs["pk"], season_current_flag=True)

        return queryset
    serializer_class = VSWDateSerializer

class FruitionSummary(APIView):

    def get(self, request, pk, format=None):
        logger.debug(self)
        sites = Site.objects.filter(farm_id=self.kwargs["pk"])
        strategy_serialized_data = []
        for site in sites:
            logger.debug(str(site.name))
            try:
                latest_reading = vsw_reading.objects.filter(site=site.id, reviewed=True).latest('date')
                logger.debug('Latest Date:' + str(latest_reading.date) + ' RZ1:' + str(latest_reading.rz1))
                strategy = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__gte=latest_reading.date)).order_by('strategy_date')[0]
                logger.debug('Strategy:' + str(strategy.strategy_date))
                strategy_serialized_data.append({
                    'site_id': site.id,
                    'latest_reading_date': latest_reading.date,
                    'latest_reading_date_rz1': latest_reading.rz1,
                    'stategy_date': strategy.strategy_date,
                    'strategy_rz1': strategy.rz1,
                    'percentage': strategy.percentage
                })

            except ObjectDoesNotExist:
                pass # No latest reading
            except IndexError:
                pass # No strategy

        data = {
            'sites': strategy_serialized_data,
            'farm_id': self.kwargs["pk"],
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
        queryset = vsw_strategy.objects.filter(site=self.kwargs["pk"], reading_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWStrategySerializer
