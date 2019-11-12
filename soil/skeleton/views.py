from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView, ListView, View

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

from .models import Probe, Reading, Site
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import re
import requests

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm, SelectorForm

from datetime import datetime

from .utils import process_probe_data

class IndexView(TemplateView):
    template_name = 'index.html'

class SiteListView(LoginRequiredMixin, ListView):
    model = Site
    template_name = 'sites.html'
    context_object_name = 'sites'

class SiteReadingsView(LoginRequiredMixin, TemplateView):
    model = Reading
    form_class = SelectorForm
    template_name = 'site_readings.html'
    #context_object_name = 'readings'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    '''
    def get_queryset(self, *args, **kwargs):

        return Reading.objects.filter(site__id=self.kwargs['pk'])
    '''
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            id = request.POST.get('site')
            logger.error('***ID:' + str(id))
            readings = Reading.objects.filter(site__id=kwargs['pk'])
            context = {'readings': readings, 'form': form}
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})

class SelectorView(TemplateView):
    form_class = SelectorForm
    template_name = 'selector.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            id = request.POST.get('site')
            logger.error('***ID:' + str(id))

        return render(request, self.template_name, {'form': form})

@login_required
def vsw_percentage(request, site_id, year, month, day):
    template = loader.get_template('vsw_percentage.html')
    context = {
        'site_id' : site_id,
        'year' : year,
        'month' : month,
        'day': day
    }
    return HttpResponse(template.render(context, request))

'''
    model_form_upload - For processing Probe and Diviner files
'''

@login_required
def model_form_upload(request):
    data = {}
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        logger.error(request.POST)
        files = request.FILES.getlist('document')

        if form.is_valid():
            for f in files:
                logger.error('***Saving File:' + str(f))
                form.save()
                try:
                    handle_file(f, request)
                    messages.success(request, "Successfully Uploaded file: " + str(f))
                except Exception as e:
                    messages.error(request, "Error with file: " + str(f) + " Error is: " + str(e))
            return redirect('model_upload')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form,
    })

'''
    handle_file - Generic file handler to create a data file as it is uploaded through a web form
'''

def handle_file(f, request):
    # File saved. Now try and process it
    logger.error('***Processing File:' + str(f))
    type = request.POST['filetype']

    file_data = ""
    try:
        for chunk in f.chunks():
            file_data = file_data + chunk.decode("utf-8")
    except Exception as e:
        logger.error(e)
    finally:
        # Call different handlers
        if type == 'neutron':
            handle_neutron_file(file_data, request)
        else:
            handle_diviner_file(file_data, request)
'''
    handle_neutron_file
'''

def handle_neutron_file(file_data, request):
    logger.error("***Handling Neutron")
    # process
    lines = file_data.split("\n")
    logger.error("Serial Line:" + lines[1])
    serialfields = lines[1].split(",")
    serialnumber = serialfields[1]
    serialnumber_formatted = serialnumber.lstrip("0")
    logger.error("Serial Number:" + serialnumber_formatted)

    # Check Serial Number exists and return error message if is not. Then get the serial number unique id
    if not Probe.objects.filter(serial_number=serialnumber_formatted).exists():
        raise Exception("Serial Number:" + serialnumber_formatted + " does not exist.")
    p = Probe.objects.get(serial_number=serialnumber_formatted)
    serial_number_id = p.id

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    readings = []

    for line in lines:
        # If Note, grab the site_id
        note = re.search("^Note,[a-zA-Z0-9_]+", line)
        reading = re.search("^\d.*", line)
        if note:
            logger.error("***We have a note line:" + line)
            # If not first note line of file
            if any(data):
                readings.reverse() # Neutron Probe files go from deepest to shallowest
                data[key].append(readings)
                readings = []
            site_line = line.split(",")
            site_number = site_line[1].rstrip()
            logger.error("Site Number:" + str(site_number))
        elif reading:
            logger.error("***We have a reading line:" + line)
            reading_line = line.split(",")
            # If first reading for note, we need to get the date and create the key
            if reading_line[0] == "1":
                # Get date part from first depth is fine. Comes in as DD/MM/YY American crap format before we get underscore time component
                date_raw = str(reading_line[10])
                datefields = date_raw.split("_")
                date = datefields[0]
                date_object = datetime.strptime(date, '%m/%d/%y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')

                key = site_number.rstrip() + "," + date_formatted
                logger.error("Key:" + key)

                if key in data:
                    logger.error("Key exists:")
                else:
                    logger.error("No Key does not exist:")
                    data[key] = []

            readings.append(float(reading_line[6]))
        else:
            logger.error("Else not valid processing line!"  + line)

        logger.error("End of Loop:")
        #logger.error("Data:" + str(data))

    data[key].append(readings) # Always insert last reading
    logger.error("Final Data submitted to process_probe_data:" + str(data))
    process_probe_data(data, serial_number_id, request)

'''
    handle_diviner_file
'''

def handle_diviner_file(file_data, request):
    logger.error("***Handling Diviner")
    lines = file_data.split("\n")

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    serial_number_id = None
    readings = []
    need_date = True

    for line in lines:
        # Site Heading line contains the special Diviner Number
        heading = re.search("^Site.*", line)
        # Seems that a reading line is the only one beginning with a number (day part of date)
        reading = re.search("^\d.*", line)

        if heading:
            logger.error("***We have a heading line:" + line)
            diviner_fields = line.split(",")
            diviner_number = diviner_fields[1]
            diviner_number_formatted = diviner_number.lstrip()
            logger.error("Diviner Number Formatted:" + diviner_number_formatted)

            # Get Serial Number and Site Number from Diviner Probe and
            try:
                site = Site.objects.get(diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a site.")
            site_number = site.site_number
            logger.error("Site Number:" + site_number)

            try:
                sn = Probe.objects.get(probediviner__diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a probe/serial number.")
            serial_number_id = sn.id
            logger.error("Serial Number ID:" + str(serial_number_id))

        elif reading:
            logger.error("***We have a reading line:" + line)
            reading_line = line.split(",")

            if need_date:
                # Handle date in dd Month YYYY 24HH:MM:SS format
                date_raw = str(reading_line[0])
                date_object = datetime.strptime(date_raw, '%d %b %Y %H:%M:%S')
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.error("Date:" + date_formatted)
                key = site_number + "," + date_formatted
                logger.error("Key:" + key)
                data[key] = []
                need_date = False

            # Always remove date as the first element
            reading_line.pop(0)
            logger.error(reading_line)
            reading_array = []
            for reading in reading_line:
                reading = reading.lstrip(' ')
                reading = reading.rstrip()
                reading_array.append(float(reading))

            data[key].append(reading_array)
        else:
            logger.error("Not a line to process:"  + line)

    logger.error("Final Data:" + str(data))
    process_probe_data(data, serial_number_id, request)
