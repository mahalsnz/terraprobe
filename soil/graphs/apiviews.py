import logging
from rest_framework import generics

from .models import vsw_reading
from .serializers import VSWSerializer, SiteSerializer, FarmSerializer, ReadingTypeSerializer

# Get an instance of a logger
logger = logging.getLogger(__name__)

class VSWReadingList(generics.ListCreateAPIView):

    def get_queryset(self):
        queryset = vsw_reading.objects.filter(site=self.kwargs["pk"])

        return queryset
    serializer_class = VSWSerializer
