from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from django.contrib import messages
from skeleton.utils import get_current_season, get_site_season_start_end

from skeleton.models import Reading, Site, Farm, WeatherStation
import os

import requests
import re

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

'''
    From command line can just run 'python manage.py request_to_hortplus --stations=HAV'
'''

class Command(BaseCommand):
    help = 'Requests data from hortplus'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--serial', type=str, help='Hortplus serial number generated individually for a user')
        parser.add_argument('-p', '--period', type=int, help='The number of records for the specified interval, counting backwards from now (unless a startdate provided)')
        parser.add_argument('-d', '--startdate', type=str, help='The date to start providing data from. This forces the period to count forwards from this date. Format YYYY-MMDD')
        parser.add_argument('-f', '--format', type=str, help='The format the resulting data should be provided as')
        parser.add_argument('-i', '--interval', type=str, help='The type of weather data. H for hourly and D for daily.')
        parser.add_argument('-t', '--stations', type=str, help='The list of weather station ids separated by a comma.')
        parser.add_argument('-m', '--metvars', type=str, help='The list of weather variable and measurement type TD_M,RN_T combined with an underscore, separated by a comma.')

    def handle(self, *args, **kwargs):

        response_text = None
        # get arguments from command line or use ones that will be done autoamtically
        serial = kwargs['serial'] if kwargs['serial'] else os.getenv('HORTPLUS_JACK_KEY')
        if kwargs['period']:
            data = {
                'period': kwargs['period'], # 7
                'format': kwargs['format'], # csv
                'interval': kwargs['interval'], # D
                'stations': kwargs['stations'], # HAV
                'metvars' : kwargs['metvars'] # RN_T
            }
            # startdate is optional
            if kwargs['startdate']:
                data['startdate'] = kwargs['startdate']
            response_text = post_request(data, serial)
        else:
            readings = Reading.objects.select_related('site__farm__weatherstation').filter(rain__isnull=True, type=1)
            for reading in readings:
                logger.debug('Reading object to process: ' + str(reading))
                season = get_current_season()
                dates = get_site_season_start_end(reading.site, season)
                # If a site has only one reading we cannot calculate the previous reading date. A try block is the only way to catch this
                try:
                    previous_reading = reading.get_previous_by_date(site=reading.site, date__range=(dates.period_from, dates.period_to))
                except:
                    previous_reading = None
                if previous_reading:
                    site = reading.site
                    farm = site.farm
                    weatherstation = farm.weatherstation

                    days = (reading.date  - previous_reading.date).days - 1
                    logger.debug('Previous Reading:' + str(previous_reading))
                    logger.debug(days)
                    startdate = previous_reading.date + timedelta(days=1)
                    logger.debug('startdate' + str(startdate))

                    data = {
                        'period': days,
                        'startdate' : str(startdate),
                        'format' : 'csv',
                        'interval': 'D',
                        'stations': weatherstation.code,
                        'metvars' : 'RN_T'
                    }
                    response_text = post_request(data, serial)

                    lines = response_text.split("\n")
                    del lines[0]
                    rainfall = 0
                    for line in lines:
                        valid = re.search("^\w.*", line) # make sure we have a valid line to split
                        if valid:
                            fields = line.split(",")
                            rainfall += float(fields[3])
                            logger.debug(str(rainfall))
                    reading.rain = round(rainfall, 1)
                    reading.save()
                else:
                    logger.debug('No previous reading for site so cannot calculate a rain reading')

'''
    post_request
'''

def post_request(data, serial):
    try:
        r = requests.post('https://hortplus.metwatch.nz/index.php?pageID=wxn_wget_post&serial=' + serial, data=data)
        if r.status_code == 200:
            logger.debug('response ' + str(r.text))
            return r.text
        else:
            raise Exception("Error processing request:" + str(r.status_code))
    except Exception as e:
        messages.error(request, "Error: " + str(e))
