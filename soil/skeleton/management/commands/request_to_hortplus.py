from django.core.management.base import BaseCommand
from django.utils import timezone
from skeleton.models import WeatherStation
import os

import requests

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

'''
    From command line can just run 'python manage.py request_to_hortplus --stations=HAV'
'''

class Command(BaseCommand):
    help = 'Requests data from hortplus'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--serial', type=str, help='Hortplus serial number generated individuall for a user')
        parser.add_argument('-p', '--period', type=int, help='The number of records for the specified interval, counting backwards from now (unless a startdate provided)')
        parser.add_argument('-d', '--startdate', type=str, help='The date to start providing data from. This forces the period to count forwards from this date. Format YYYY-MMDD')
        parser.add_argument('-f', '--format', type=str, help='The format the resulting data should be provided as')
        parser.add_argument('-i', '--interval', type=str, help='The type of weather data. H for hourly and D for daily.')
        parser.add_argument('-t', '--stations', type=str, help='The list of weather station ids separated by a comma.')
        parser.add_argument('-m', '--metvars', type=str, help='The list of weather variable and measurement type TD_M,RN_T combined with an underscore, separated by a comma.')

    def handle(self, *args, **kwargs):
        # get arguments from command line or use ones that will be done autoamtically
        serial = kwargs['serial'] if kwargs['serial'] else os.getenv('HORTPLUS_JACK_KEY')
        period = kwargs['period'] if kwargs['period'] else 7
        startdate = kwargs['startdate'] if kwargs['startdate'] else 'Todays date'
        format = kwargs['format'] if kwargs['format'] else 'csv'
        interval = kwargs['interval'] if kwargs['interval'] else 'D'
        stations = kwargs['stations'] if kwargs['stations'] else None
        metvars = kwargs['metvars'] if kwargs['metvars'] else 'RN_T'
        logger.debug('serial=' + serial)
        logger.debug('period=' + str(period))
        data = {
            'period': period,
            'format': format,
            'interval': interval,
            'stations': stations,
            'metvars' : metvars
        }
        logger.debug(data)
        try:
            r = requests.post('https://hortplus.metwatch.nz/index.php?pageID=wxn_wget_post&serial=' + serial, data=data)
            if r.status_code == 200:
                logger.debug('response ' + str(r.text))
            else:
                raise Exception("Error processing request:" + str(r.status_code))
        except Exception as e:
            messages.error(request, "Error: " + str(e))


        #WeatherStation.objects.all()
