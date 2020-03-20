import logging
from rest_framework import generics

from .models import vsw_reading, vsw_strategy
from .serializers import VSWSerializer, SiteSerializer, FarmSerializer, ReadingTypeSerializer, VSWStrategySerializer

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWReadingList(generics.ListCreateAPIView):

    def get_queryset(self):
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_reading.objects.filter(site=self.kwargs["pk"], date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWSerializer

class VSWStrategyList(generics.ListCreateAPIView):

    def get_queryset(self):
        #r = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('-date').first()
        queryset = vsw_strategy.objects.filter(site=self.kwargs["pk"], reading_date__range=(self.kwargs["period_from"], self.kwargs["period_to"]))

        return queryset
    serializer_class = VSWStrategySerializer
