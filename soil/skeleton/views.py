from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView, ListView

from django.shortcuts import render
from django.shortcuts import redirect
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

from .forms import DocumentForm

from datetime import datetime

from .utils import process_probe_data

class IndexView(TemplateView):
    template_name = 'index.html'

class SiteListView(LoginRequiredMixin, ListView):
    model = Site
    template_name = 'sites.html'
    context_object_name = 'sites'

class SiteReadingsView(LoginRequiredMixin, ListView):
    model = Reading
    template_name = 'site_readings.html'
    context_object_name = 'readings'
    
    def get_queryset(self, *args, **kwargs):
        return Reading.objects.filter(site__id=self.kwargs['pk'])

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
                    messages.success(request, "Successfully Uploaded")
                except Exception as e:
                    messages.error(request, e)
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
        if type == 'probe':
            handle_probe_file(file_data, request)
        else:
            handle_diviner_file(file_data, request)
'''
    handle_probe_file

    Structure of data we are creating

    data = {
        '3306,28-5-2019' : [
            # First reading (of usually 3)
            [
                3456, # First HA (depth reading) This is reversed and first HA will actually be deepest depth
                1111,
                1234
            ],
            # Second reading
            [
                1,
                1,
                4
            ]
            # Third reading
            [
                1234,
                515342,
                341234
            ]
        ]
    }
'''

def handle_probe_file(file_data, request):
    logger.error("***Handling Probe")
    # process
    lines = file_data.split("\n")
    logger.error("Serial Line:" + lines[1])
    serialfields = lines[1].split(",")
    serialnumber = serialfields[1]
    serialnumber_formatted = serialnumber.lstrip("0")
    logger.error("Serial Number:" + serialnumber_formatted)

    # TODO: Check Serial Number exists and return error message if it has not and then get the serial number unique id and then
    if not Probe.objects.filter(serial_number=serialnumber_formatted).exists():
        raise Exception("Serial Number:" + serialnumber_formatted + " does not exist.")
    p = Probe.objects.get(serial_number=serialnumber_formatted)

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
                data[key].append(readings)
                readings = []
            site_line = line.split(",")
            site_number = site_line[1].rstrip()
            logger.error("Site Number:" + str(site_number))
        elif reading:
            logger.error("***We have a reading line:" + line)
            reading_line = line.split(",")
            logger.error("***First element of reading line" + reading_line[0])
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

            readings.append(reading_line[6])

        else:
            logger.error("Else not valid processing line!"  + line)

        logger.error("End of Loop:")
        logger.error("Data:" + str(data))
    logger.error("Outside of Loop:")
    data[key].append(readings) # Always insert last reading
    logger.error("Final Data:" + str(data))
    process_probe_data(data, p.id, request)

'''
    handle_diviner_file
'''

def handle_diviner_file(file_data, datafile):
    logger.error("***Handling Diviner")
    lines = file_data.split("\n")

    need_date = True

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    readings = []

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
            logger.error("Site Number:" + site.site_number)

            try:
                sn = Probe.objects.get(probediviner__diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a probe/serial number.")
            logger.error("Serial Number:" + sn.serial_number)

        elif reading:
            logger.error("***We have a reading line:" + line)
            reading_line = line.split(",")

            if need_date:
                # Handle date in dd Month YYYY 24HH:MM:SS format
                date_raw = str(reading_line[0])
                date_object = datetime.strptime(date_raw, '%d %b %Y %H:%M:%S')
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.error("Date:" + date_formatted)
                need_date = False

            # Always remove date as the first element
            reading_line.pop(0)
            logger.error(reading_line)
            for reading in reading_line:
                print(reading.lstrip(' '))
        else:
            logger.error("Not a line to process:"  + line)
