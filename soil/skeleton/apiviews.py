from rest_framework import generics

from .models import Report, Season, Farm, Reading, Site, ReadingType
from address.models import Address, Locality, State, Country
from .serializers import CountrySerializer, StateSerializer, LocalitySerializer, AddressSerializer, ReportSerializer, SeasonSerializer, FarmSerializer \
, ReadingSerializer, SiteSerializer, ReadingTypeSerializer

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

class ReadingDetail(generics.RetrieveDestroyAPIView):
    queryset = Reading.objects.all();
    serializer_class = ReadingSerializer

class SiteReadingList(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = Site.objects.filter(id=self.kwargs["pk"])
        return queryset
    serializer_class = SiteSerializer
