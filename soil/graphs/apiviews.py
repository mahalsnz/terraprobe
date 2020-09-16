import logging
from rest_framework import generics

from .models import vsw_reading, vsw_strategy
from skeleton.models import Farm, Site, SeasonStartEnd
from .serializers import VSWSerializer, SiteSerializer, FarmSerializer, ReadingTypeSerializer, VSWStrategySerializer, VSWDateSerializer, FruitionSummarySerializer
from django.db.models import Q

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWDateList(generics.ListAPIView):

    def get_queryset(self):
        queryset = SeasonStartEnd.objects.filter(site=self.kwargs["pk"], season_current_flag=True)

        return queryset
    serializer_class = VSWDateSerializer

class FruitionSummary(generics.ListAPIView):

    def get_queryset(self):

        # Get latest date
        #Reading.objects.filter(site=site, type__name='Probe', date__range=(dates.period_from, dates.period_to)).latest('date')

        #farm = vsw_reading.objects.filter(farm=self.kwargs["pk"]).order_by('site_id').distinct('site_id')
        sites = Site.objects.filter(farm_id=self.kwargs["pk"]).distinct()
        missing_sites = vsw_strategy.objects.none()
        for site in sites:
            logger.debug(str(site.name))
            # We need the latest reading date from vsw_readings
            latest_reading = vsw_reading.objects.filter(site=site.id).latest('date')
            logger.debug(str(latest_reading.date))

            # We now need the strategy record that the latest reading is between
            pk = vsw_strategy.objects.filter(site=latest_reading.site).filter(Q(strategy_date__lte=latest_reading.date), Q(strategy_date__gte=latest_reading.date))
            #objects.filter(Q(drop_off__gte=start_date), Q(pick_up__lte=end_date))
            logger.debug(str(pk.query))
            missing_sites |= pk
            #missing_sites |= readings
        #logger.debug(str(farm.rz1))

        queryset = vsw_reading.objects.filter(farm=self.kwargs["pk"])
        return missing_sites
    serializer_class = FruitionSummarySerializer

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
