from django.http import HttpResponse
from django.template import loader

from rest_pandas import PandasView
from .models import Reading, Site, ReadingType
from .serializers import ReadingSerializer, SiteSerializer, ReadingTypeSerializer

def index(request):
    template = loader.get_template('skeleton/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

class GraphView(PandasView):
    def get_queryset(self):
        queryset = Site.objects.filter(id=self.kwargs["pk"])
        return queryset
    serializer_class = SiteSerializer
