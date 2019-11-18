from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView, ListView, View, CreateView
from django.utils import timezone

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

from .models import Probe, Reading, Site, SeasonStartEnd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import re
import requests

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm, SiteReadingsForm

from datetime import datetime

from .utils import process_probe_data

class IndexView(TemplateView):
    template_name = 'index.html'

#TODO why CreateView and not Template View
class SiteReadingsView(LoginRequiredMixin, CreateView):
    model = Reading
    form_class = SiteReadingsForm
    template_name = 'site_readings.html'

def load_sites(request):
    technician_id = request.GET.get('technician')
    sites = Site.objects.filter(technician_id=technician_id).order_by('name')
    return render(request, 'site_dropdown_list_options.html', {'sites':sites})

def load_site_readings(request):
    readings = None
    try:
        site_id = request.GET.get('site')
        season_id = request.GET.get('season')

        if site_id:
            try:
                dates = SeasonStartEnd.objects.get(site=site_id, season=season_id)
            except:
                raise Exception("No Season Start and End set up for site.")

            readings = Reading.objects.filter(site__seasonstartend__site=site_id, site__seasonstartend__season=season_id, date__range=(dates.period_from, dates.period_to)).order_by('date')

    except Exception as e:
        messages.error(request, " Error is: " + str(e))
    return render(request, 'site_readings_list.html', {'readings':readings})

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
            logger.error('***Form not valid:' + str(form))
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
        elif type == 'diviner':
            handle_diviner_file(file_data, request)
        else:
            handle_prwin_file(file_data, request)
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

'''
    handle_prwin_file
'''

def handle_prwin_file(file_data, request):
    logger.error("***Handling PRWIN")
    lines = file_data.split("\n")

    # Remove first line heading
    del lines[0]

    data = {}
    site_number = None
    serial_number_id = None
    bolNeedSerialNumber = True

    for line in lines:
        reading = re.search("^\d.*", line) # Make sure we have a reading line
        if reading:

            fields = line.split(",")

            # First field of every line is site number
            site_number = fields[0]
            logger.error("Site Number:" + site_number)
            reading_type = fields[1]
            logger.error("Type:" + reading_type)

            # We only want 'Probe' reading types
            if reading_type == 'Probe':
                # Get date part. Comes in as DD/MM/YYYY before we get 'space character' time component
                date_raw = str(fields[2])
                datefields = date_raw.split(" ")
                date = datefields[0]
                date_object = datetime.strptime(date, '%d/%m/%Y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.error("Date:" + date_formatted)

                # Get Serial Number. We are just going to get it once and asume all PRWIN readings for the season are from one probe
                if bolNeedSerialNumber:
                    serialnumber = fields[13]
                    logger.error("Serial Number:" + serialnumber)
                    serialnumber = int(serialnumber)
                    # Check Serial Number exists and return error message if is not. Then get the serial number unique id
                    if not Probe.objects.filter(serial_number=serialnumber).exists():
                        raise Exception("Serial Number:" + serialnumber + " does not exist.")
                    p = Probe.objects.get(serial_number=serialnumber)
                    serial_number_id = p.id
                    bolNeedSerialNumber = False

                # Create Key
                key = site_number + "," + date_formatted
                logger.error("Key:" + key)

                reading_array = []
                data[key] = []
                for depth in range(3, 13):
                    reading = float(fields[depth])
                    #logger.error("Reading:" + reading)
                    reading_array.append(reading)

                #logger.error("Reading Array:" + str(reading_array))

                # Wierldy enough we make 3 of these arrays to put in data to match nuetron and diviner
                for lap in range(3):
                    data[key].append(reading_array)

        # End if we have a reading
    # End loop through lines
    #logger.error("Final Data:" + str(data))
    process_probe_data(data, serial_number_id, request)
