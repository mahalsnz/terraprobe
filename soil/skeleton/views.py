from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm

class IndexView(TemplateView):
    template_name = 'index.html'

def simple_upload(request):
    template = loader.get_template('simple_upload.html')
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return render(request, 'simple_upload.html', {
            'uploaded_file_url' : uploaded_file_url
        })
    return render(request, 'simple_upload.html')

# Upload and process PSD files
def model_form_upload(request):
    data = {}
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            logger.error("*******saved file*****")
            handle_files(request.FILES['document'])
            return redirect('model_upload')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })

def handle_files(f):
    # File saved. Now try and process it
    file_data = ""
    try:
        logger.error("*******processing file*****")
        logger.error(f)

        file_data
        for chunk in f.chunks():
            #logger.error(chunk.decode("utf-8"))
            file_data = file_data + chunk.decode("utf-8")
        #file_data = f.read().decode("utf-8")
        #logger.error(file_data)
        #lines = file_data.split("\n")
        #for line in lines:
        #    logger.error(line)
    except Exception as e:
        logger.error(e)
    finally:
        logger.error(file_data)





'''
from rest_pandas import PandasView
from .models import Reading, Site, ReadingType
from .serializers import ReadingSerializer, SiteSerializer, ReadingTypeSerializer

class GraphView(PandasView):
    def get_queryset(self):
        queryset = Site.objects.filter(id=self.kwargs["pk"])
        return queryset
    serializer_class = SiteSerializer
'''
