import logging
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize

from .models import Report, Season, Farm, Reading, Site, ReadingType, SeasonStartEnd
from address.models import Address, Locality, State, Country
from .serializers import CountrySerializer, StateSerializer, LocalitySerializer, AddressSerializer, ReportSerializer, SeasonSerializer, FarmSerializer \
, ReadingSerializer, SiteSerializer, ReadingTypeSerializer
from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
logger = logging.getLogger(__name__)

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
