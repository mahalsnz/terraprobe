import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from .models import Report, Season, Farm, Reading, Site, ReadingType, SeasonStartEnd
from address.models import Address, Locality, State, Country
from .serializers import CountrySerializer, StateSerializer, LocalitySerializer, AddressSerializer, ReportSerializer, SeasonSerializer, FarmSerializer \
, ReadingSerializer, SiteSerializer, ReadingTypeSerializer
from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ReportList(generics.ListCreateAPIView):
    queryset = Report.objects.all();
    serializer_class = ReportSerializer

class ReportDetail(generics.RetrieveDestroyAPIView):
    queryset = Report.objects.all();
    serializer_class = ReportSerializer

class SeasonList(generics.ListCreateAPIView):
    queryset = Season.objects.all();
    serializer_class = SeasonSerializer

class SeasonDetail(generics.RetrieveDestroyAPIView):
    queryset = Season.objects.all();
    serializer_class = SeasonSerializer

class ReadingTypeList(generics.ListCreateAPIView):
    queryset = ReadingType.objects.all();
    serializer_class = ReadingTypeSerializer

class ReadingTypeDetail(generics.RetrieveDestroyAPIView):
    queryset = ReadingType.objects.all();
    serializer_class = ReadingTypeSerializer

class FarmList(generics.ListCreateAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

class FarmDetail(generics.RetrieveDestroyAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

class SiteList(generics.ListCreateAPIView):
    queryset = Site.objects.all();
    serializer_class = SiteSerializer

class SiteDetail(generics.RetrieveDestroyAPIView):
    queryset = Site.objects.all();
    serializer_class = SiteSerializer

class ReadingList(generics.ListCreateAPIView):
    queryset = Reading.objects.all();
    serializer_class = ReadingSerializer

class ReadingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reading.objects.all();
    serializer_class = ReadingSerializer

class SiteReadingList(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = Site.objects.filter(id=self.kwargs["pk"])
        return queryset
    serializer_class = SiteSerializer

class EOYFarmSummary(APIView):

    def get(self, request, farm_id, format=None):
        logger.debug(str(request.GET))

        farms = Farm.objects.filter(id=farm_id)
        eoy_data = []
        averge_rainfall = 200

        for farm in farms:
            sites = Site.objects.filter(farm=farm)

            for site in sites:
                seasons = SeasonStartEnd.objects.filter(site_id=site.id).order_by('period_from')

                previous_rainfall = 0.0
                previous_irrigation_mms = 0.0
                previous_eff_rain = 0.0
                previous_irrigation_litres = 0.0

                rain_diff = 0.0
                irrigation_mms_diff = 0.0
                eff_rain_diff = 0.0
                irrigation_litres_diff = 0.0

                for season in seasons:
                    readings = Reading.objects.filter(site=site.id, type=1, date__range=(season.period_from, season.period_to)).order_by('date')

                    rainfall = readings.aggregate(rain__sum=Coalesce(Sum('rain'), 0))
                    rain_sum = rainfall.get('rain__sum')

                    irrigation_litres = readings.aggregate(irrigation_litres__sum=Coalesce(Sum('irrigation_litres'), 0))
                    irrigation_litres_sum = irrigation_litres.get('irrigation_litres__sum')

                    irrigation_mms = readings.aggregate(irrigation_mms__sum=Coalesce(Sum('irrigation_mms'), 0))
                    irrigation_mms_sum = irrigation_mms.get('irrigation_mms__sum')

                    eff_rain = readings.aggregate(effective_rainfall__sum=Coalesce(Sum('effective_rainfall'), 0))
                    eff_rain_sum = eff_rain.get('effective_rainfall__sum')

                    if previous_rainfall:
                        rain_diff = round(rain_sum - previous_rainfall)
                        logger.debug('Rainfall Diff from last year:' + str(rain_diff))
                    previous_rainfall = rain_sum

                    if previous_eff_rain:
                        eff_rain_diff = round(eff_rain_sum - previous_eff_rain)
                        logger.debug('eff_rain Diff from last year:' + str(eff_rain_diff))
                    previous_eff_rain = eff_rain_sum

                    if previous_irrigation_mms:
                        irrigation_mms_diff = round(irrigation_mms_sum - previous_irrigation_mms)
                        logger.debug('irrigation_mms Diff from last year:' + str(irrigation_mms_diff))
                    previous_irrigation_mms = irrigation_mms_sum

                    if previous_irrigation_litres:
                        irrigation_litres_diff = round(irrigation_litres_sum - previous_irrigation_litres)
                        logger.debug('irrigation_litres Diff from last year:' + str(irrigation_litres_diff))
                    previous_irrigation_litres = irrigation_litres_sum

                    logger.debug('Season: ' + str(season.season_name) + ' Farm:' + str(farm.name) + ' Site:' + str(site.site_number) + ' Rainfall:' + str(rain_sum))

                    eoy_data.append({
                        "farm": farm.name,
                        'site' : site.name,
                        'site_id' : site.id,
                        'season': season.season_name,
                        'rain': rain_sum,
                        'rain_diff': rain_diff,
                        'irrigation_litres': irrigation_litres_sum,
                        'irrigation_litres_diff': irrigation_litres_diff,
                        'irrigation_mms': irrigation_mms_sum,
                        'irrigation_mms_diff': irrigation_mms_diff,
                        'eff_rain' : eff_rain_sum,
                        'eff_rain_diff' : eff_rain_diff,
                    })

        #reorder data
        eoy_data.reverse()

        data = {
            'eoy_data': eoy_data,
        }

        return Response(eoy_data)
