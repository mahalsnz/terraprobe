from rest_framework import generics

from .models import Farm, Reading, Site, ReadingType
from .serializers import FarmSerializer, ReadingSerializer, SiteSerializer, ReadingTypeSerializer

class FarmList(generics.ListCreateAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

class FarmDetail(generics.RetrieveDestroyAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

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
