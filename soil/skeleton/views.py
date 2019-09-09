from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

from .models import Probe

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
            form.save()
            logger.error("*******saved file*****")
            try:
                handle_file(request)
            except Exception as e:
                messages.error(request, e)
            finally:
                return redirect('model_upload')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form,
    })

'''
    handle_file - Generic file handler to create a data file as it is uploaded through a web form
'''

def handle_file(request):
    # File saved. Now try and process it
    f = request.FILES['document']
    type = request.POST['filetype']

    file_data = ""
    try:
        logger.error("*******processing file*****")
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
    logger.error("****Handling Probe")
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
    site = None
    readings = []

    for line in lines:
        # If Note, grab the site_id
        note = re.search("^Note,\d+", line)
        reading = re.search("^\d.*", line)
        if note:
            logger.error("***We have a note line:" + line)
            site_line = line.split(",")
            site = site_line[1].rstrip()
            logger.error("Site Id:" + str(site))
        if reading:
            logger.error("***We have a reading line:" + line)
            reading_line = line.split(",")
            logger.error("***First element of reading line" + reading_line[0])
            if reading_line[0] == "1":
                # Get date part from first depth is fine. Comes in as DD/MM/YY_crap get before underscore
                date_raw = str(reading_line[10])
                datefields = date_raw.split("_")
                date = datefields[0]
                date_object = datetime.strptime(date, '%m/%d/%y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')

                key = site.rstrip() + "," + date_formatted
                logger.error("Key:" + key)

                if key in data:
                    logger.error("Key exists:")
                    data[key].append(readings)
                    readings = []
                else :
                    logger.error("No Key does not exect:")
                    data[key] = []
            readings.append(reading_line[6])
            logger.error("Data:" + str(data))
        else:
            logger.error("Else not valid processing line!")

        logger.error("End of Loop:")

    logger.error("Outside of Loop:")
    data[key].append(readings) # Always insert last reading
    logger.error("Final Data:" + str(data))
    process_probe_data(data, p.id, request)

'''
    process_probe_data
'''

def process_probe_data(readings, serial_unique_id, request):

    for key, site_info in readings.items():
        # Firstly we total up each site-dates readings
        totals = {}
        split_key = key.split(",")

        for depth_arr in site_info:
            for index in range(len(depth_arr)):
                print(depth_arr[index])
                if index in totals:
                    totals[index] = int(totals[index]) + int(depth_arr[index])
                else:
                    totals[index] = int(depth_arr[index])

        # Secondly we average out each reading from the amount of readings taken
        averaged_totals = []
        readings_taken = len(site_info)
        for key, value in totals.items():
            print("value:" + str(value) + " readings_taken:" + str(readings_taken))
            averaged_totals.append(int(value) / int(readings_taken))

        # Thirdly we reverse thate order of averaged_totals
        averaged_totals.reverse()
        print(averaged_totals)

        # create data object in the way we want
        data = {}
        data['date'] = split_key[1]
        data['created_by'] = '2'
        data['site'] = '3'
        data['serial_number'] = serial_unique_id
        data['type'] = '1'

        for index in range(len(averaged_totals)):
            data['depth' + str(index + 1)] = averaged_totals[index]

        logger.error("Ready to insert:" + str(data))

        if data:
            # TODO: Add unique key on readings table for date, reading_type and site
            logger.error("Post data if something in data" + str(data))
            host = request.get_host()
            headers = {'contentType': 'application/json'}
            r = requests.post('http://' + host + '/api/reading/', headers=headers, data=data)
            logger.error('request response' + r.text)
            data = {}

    logger.error("Outside of Process Data Loop:")

'''
    handle_diviner_file
'''

def handle_diviner_file(datafile):
    logger.error("Handling Diviner")
