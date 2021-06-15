from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from django.contrib import messages
from skeleton.utils import get_current_season, get_site_season_start_end

from skeleton.models import Reading, Site, Farm, WeatherStation, Season
import os
import json
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
        parser.add_argument('-P', '--purpose', type=str, help='One of process_readings or generate_eoy_data')
        parser.add_argument('-s', '--serial', type=str, help='Hortplus serial number generated individually for a user')
        parser.add_argument('-p', '--period', type=int, help='The number of records for the specified interval, counting backwards from now (unless a startdate provided)')
        parser.add_argument('-d', '--startdate', type=str, help='The date to start providing data from. This forces the period to count forwards from this date. Format YYYY-MMDD')
        parser.add_argument('-f', '--format', type=str, help='The format the resulting data should be provided as')
        parser.add_argument('-i', '--interval', type=str, help='The type of weather data. H for hourly and D for daily.')
        parser.add_argument('-t', '--stations', type=str, help='The list of weather station ids separated by a comma.')
        parser.add_argument('-m', '--metvars', type=str, help='The list of weather variable and measurement type TD_M,RN_T combined with an underscore, separated by a comma.')
        parser.add_argument('--sites', type=open, help='A list of sites to get request rainfall for.')

    def handle(self, *args, **kwargs):
        response_text = None
        # get arguments from command line or use ones that will be done autoamtically
        serial = kwargs['serial'] if kwargs['serial'] else os.getenv('HORTPLUS_JACK_KEY')
        if kwargs['purpose'] is None:
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
        elif kwargs['purpose'] == 'process_readings':
            logger.info('Start processing of readings')
            readings = None
            if kwargs['sites']:
                sites = kwargs['sites']
                logger.info('Starting update of rainfall for sites that have just been uploaded and have a null rain reading.' + str(sites))
                readings = Reading.objects.select_related('site__farm__weatherstation').filter(site__in=sites, rain__isnull=True, type=1)
            else:
                logger.info('Starting update of rainfall for all sites that have a null rain reading')
                readings = Reading.objects.select_related('site__farm__weatherstation').filter(rain__isnull=True, type=1)
            for reading in readings:
                logger.debug('Reading object to process: ' + str(reading))
                season = get_current_season()
                dates = get_site_season_start_end(reading.site, season)

                # If a site has only one reading we cannot calculate the previous reading date. A try block is the only way to catch this
                try:
                    previous_reading = reading.get_previous_by_date(site=reading.site, type=1, date__range=(dates.period_from, dates.period_to))
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
                            if fields[3] != '-' and fields[3] != '.':
                                rainfall += float(fields[3])
                            logger.debug(str(rainfall))
                    reading.rain = round(rainfall, 1)
                    reading.save()
                else:
                    logger.debug('No previous reading for site so cannot calculate a rain reading')
        elif kwargs['purpose'] == 'generate_eoy_data':
            rain_data = {} # Keyed by the weatherstation code and the value will be the sum of rain / 10 years
            #current_rain_data = {}
            start_dates = [] # 10 start dates starting at the 1st October of current year. Actually 2nd cause of the way API works

            season = Season.objects.get(current_flag=True)
            current_year = season.formatted_season_start_year
            current_year_date = str(current_year) + '-10-02'
            start_dates.append(current_year_date)

            station = kwargs['stations']
            logger.debug("Generating average rainfall for last 10 years back from " + current_year_date + " for station " + station)

            for month in ['10','11','12','01','02','03','04','05','06']:
                rain_data[month] = {
                    'avg' : 0,
                    'cur' : 0
                }

            x = 0
            while x < 10:
                year = (int(current_year) -1) - x
                # Start Date will always be 1st of October of year we got for current.
                date = str(year) + '-10-02'
                start_dates.append(date)
                x = x + 1
            logger.debug('We will be getting rainfall data for ' + str(start_dates) + ' + 272 days')

            # We will have the current year, and the previous 10 years in array
            for start_date in start_dates:
                data = {
                    'period': 272, # 272 days will take us to 30th of June (except leap years but don't need to be exact)
                    'startdate' : start_date,
                    'format' : 'csv',
                    'interval': 'D',
                    'stations': station,
                    'metvars' : 'RN_T'
                }

                response_text = post_request(data, serial)

                lines = response_text.split("\n")
                del lines[0]
                for line in lines:
                    valid = re.search("^\w.*", line) # make sure we have a valid line to split
                    if valid:
                        fields = line.split(",")
                        station = fields[0]
                        start = fields[1]
                        split_start = start.split("-") # Split from date "2019-10-17 08:00:00"
                        month = split_start[1] # Month which is the key to our rain_data dict is the second part of date
                        rain = fields[3]
                        if rain != '-' and rain != '.':
                            if start_date == current_year_date:
                                rain_data[month]['cur'] += float(rain)
                            else:
                                rain_data[month]['avg'] += float(rain)
                        else:
                            logger.error("Unidentifiable value for rain of:" + rain)

            return json.dumps(rain_data)
        else:
            logger.error('Unidentified purpose of requesting hortplus data')

'''
    post_request
'''

def post_request(data, serial):
    try:
        r = requests.post('https://hortplus.metwatch.nz/index.php?pageID=wxn_wget_post&serial=' + serial, data=data)
        logger.debug('data in request ' + str(data))
        if r.status_code == 200:
            logger.debug('response ' + str(r.text))
            return r.text
        else:
            raise Exception("Error processing request:" + str(r.text))
    except Exception as e:
        messages.error(request, "Error: " + str(e))
