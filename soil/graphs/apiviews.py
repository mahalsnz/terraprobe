import logging
from rest_framework import generics

from .models import vsw_reading, vsw_strategy
from skeleton.models import SeasonStartEnd
from .serializers import VSWSerializer, SiteSerializer, FarmSerializer, ReadingTypeSerializer, VSWStrategySerializer, VSWDateSerializer

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWDateList(generics.ListAPIView):

    def get_queryset(self):
        queryset = SeasonStartEnd.objects.filter(site=self.kwargs["pk"], season_current_flag=True)

        return queryset
    serializer_class = VSWDateSerializer

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
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_strategy.objects.filter(site=self.kwargs["pk"], reading_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWStrategySerializer
