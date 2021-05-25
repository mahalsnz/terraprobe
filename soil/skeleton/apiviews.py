import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from .models import Report, Season, Farm, Reading, Site, ReadingType, SeasonStartEnd, SeasonalSoilStat
from address.models import Address, Locality, State, Country
from .serializers import CountrySerializer, StateSerializer, LocalitySerializer, AddressSerializer, ReportSerializer, SeasonSerializer, FarmSerializer \
, ReadingSerializer, SiteSerializer, ReadingTypeSerializer
from skeleton.utils import get_current_season, get_site_season_start_end, get_soil_type, calculate_seasonal_soil_stat

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

        # Checks each season and calculates stats if not there
        calculate_seasonal_soil_stat()

        farms = Farm.objects.select_related('weatherstation').filter(id=farm_id)
        eoy_data = []
        for farm in farms:
            average_rainfall = farm.weatherstation.average_rainfall
            sites = Site.objects.select_related('product__crop').select_related('product__variety').filter(farm=farm)

            for site in sites:
                seasons = SeasonStartEnd.objects.filter(site_id=site.id).order_by('period_from')

                previous_irrigation_mms = 0.0
                previous_eff_rain = 0.0

                rain_diff = 0.0
                rain_perc = 0.0

                irrigation_mms_diff = 0.0
                irrigation_mms_perc = 0.0

                eff_irrigation_diff = 0.0
                eff_irrigation_perc = 0.0

                average_eff_irrigation_diff = 0.0

                for season in seasons:
                    readings = Reading.objects.filter(site=site.id, type__name="Probe", date__range=(season.period_from, season.period_to)).order_by('date')
                    full_point = Reading.objects.get(site=site.id, type__name="Full Point", date__range=(season.period_from, season.period_to))

                    soil_type = get_soil_type(full_point.rz1)
                    stats = SeasonalSoilStat.objects.get(season=season.season, soil_type=soil_type)
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

                    rain_diff = round(rain_sum - average_rainfall)
                    rain_perc = round(rain_sum / average_rainfall * 100)
                    logger.debug('Rainfall Diff from average:' + str(rain_diff) + ' % Diff ' + str(rain_perc))

                    eff_irrigation_perc = (eff_irrigation_sum / irrigation_mms_sum * 100)
                    logger.debug('Effective Irrigation %:' + str(eff_irrigation_perc))

                    if previous_irrigation_mms:
                        irrigation_mms_diff = round(irrigation_mms_sum - previous_irrigation_mms)
                        irrigation_mms_perc = round(irrigation_mms_sum / previous_irrigation_mms * 100)
                        logger.debug('irrigation_mms Diff from last year:' + str(irrigation_mms_diff) + ' % Diff ' + str(irrigation_mms_perc))
                    previous_irrigation_mms = irrigation_mms_sum

                    average_eff_irrigation_diff = average_eff_irrigation_perc - eff_irrigation_perc

                    logger.debug('Season: ' + str(season.season_name) + ' Farm:' + str(farm.name) + ' Weatherstation ' + farm.weatherstation.name +
                        ' Site:' + str(site.site_number) + ' Rainfall:' + str(rain_sum))

                    eoy_data.append({
                        "farm": farm.name,
                        'average_rainfall': average_rainfall,
                        'site' : site.name,
                        'site_id' : site.id,
                        'season': season.season_name,
                        'period_from' : season.period_from,
                        'period_to' : season.period_to,
                        'soil_type' : soil_type,
                        'product' : site.product.crop.name + ' - ' + site.product.variety.name,
                        'rz1' : site.rz1_bottom,
                        'application_rate' : site.application_rate,
                        'rain': rain_sum,
                        'rain_perc': rain_perc,
                        'rain_diff': rain_diff,
                        'irrigation_mms': irrigation_mms_sum,
                        'irrigation_mms_perc': irrigation_mms_perc,
                        'irrigation_mms_diff': irrigation_mms_diff,
                        'eff_irrigation' : eff_irrigation_sum,
                        'eff_irrigation_diff' : eff_irrigation_diff,
                        'eff_irrigation_perc' : eff_irrigation_perc,
                        'average_eff_irrigation' : average_eff_irrigation,
                        'average_eff_irrigation_diff' : average_eff_irrigation_diff,
                        'average_eff_irrigation_perc' : average_eff_irrigation_perc
                    })

        #reorder data
        eoy_data.reverse()

        data = {
            'eoy_data': eoy_data,
        }

        return Response(eoy_data)
