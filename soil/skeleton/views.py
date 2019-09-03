from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

import re
import requests

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm#
from datetime import datetime

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
        })#
    return render(request, 'simple_upload.html')

'''
    model_form_upload - For processing Probe and Diviner files
'''

def model_form_upload(request):
    data = {}
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        logger.error(request.POST)
        if form.is_valid():
            filetype = request.POST['filetype']
            form.save()
            logger.error("*******saved file*****")
            handle_file(request.FILES['document'], filetype)
            return redirect('model_upload')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form#
    })

'''
    handle_file - Generic file handler to create a data file as it is uploaded through a web form
'''

def handle_file(f, type):
    # File saved. Now try and process it
    file_data = ""
    try:
        logger.error("*******processing file*****")
        for chunk in f.chunks():
            #logger.error(chunk.decode("utf-8"))
            file_data = file_data + chunk.decode("utf-8")
    except Exception as e:
        logger.error(e)
    finally:
        # Call different handlers
        if type == 'probe':
            handle_probe_file(file_data)
        else:
            handle_diviner_file(file_data)
'''
    handle_probe_file
'''

def handle_probe_file(file_data):
    logger.error("****Handling Probe")
    # process
    lines = file_data.split("\n")
    logger.error("Serial Line:" + lines[1])
    serialfields = lines[1].split(",")
    serialnumber = serialfields[1]
    serialnumber_formatted = serialnumber.lstrip("0")
    logger.error("Serial Number:" + serialnumber_formatted)

    # TODO: Serial Number lookup for site id

    data = {}
    for line in lines:
        digit = re.search("^\d", line)

        if digit:
            # If one is first element we have a new reading record
            readingfields = line.split(",")

            #logger.error("Depth:" + str(readingfields[0]))
            if int(readingfields[0]) == 1:
                logger.error("create new record:" + str(data))
                # Get date part from first depth is fine. Comes in as DD/MM/YY_crap get before underscore
                date_raw = str(readingfields[10])
                datefields = date_raw.split("_")
                date = datefields[0]
                date_object = datetime.strptime(date, '%m/%d/%y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.error("Date:" + date)
                data['depth1'] = str(readingfields[6])
                data['date'] = date_formatted
                data['created_by'] = '2'
                data['site'] = '3'
                data['serial_number'] = '1'
                data['type'] = '1'
                #data['created_date'] = "2019-08-22T14:06:51.521917+12:00"
            else:
                #depthkey = 'depth' + str(readingfields[0])
                data['depth' + str(readingfields[0])] = str(readingfields[6])
        else:
            if data:
                logger.error("Post data if something in data" + str(data))
                headers = {'contentType': 'application/json'}
                r = requests.post('http://127.0.0.1:8000/api/reading/', headers=headers, data=data)
                logger.error('request response' + r.text)
                data = {}

'''
    handle_diviner_file
'''

def handle_diviner_file(datafile):
    logger.error("Handling Diviner")






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
