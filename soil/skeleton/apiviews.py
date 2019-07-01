from rest_framework import generics

from .models import Farm, Reading
from .serializers import FarmSerializer, ReadingSerializer

class FarmList(generics.ListCreateAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

class FarmDetail(generics.RetrieveDestroyAPIView):
    queryset = Farm.objects.all();
    serializer_class = FarmSerializer

class ReadingList(generics.ListCreateAPIView):
    queryset = Farm.objects.all();
    serializer_class = ReadingSerializer

class ReadingDetail(generics.RetrieveDestroyAPIView):
    queryset = Reading.objects.all();
    serializer_class = ReadingSerializer
