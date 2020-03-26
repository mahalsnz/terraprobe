import requests
import statistics
from django.core.exceptions import ObjectDoesNotExist

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site, Reading, Season, SeasonStartEnd

'''
    Takes a season and finds the previous season to it (number descinding) 2014 returnd 2013
    Returns a Season object
'''

def get_previous_season(season):
    try:
        previous_season = Season.objects.filter(name__lt=season).order_by('-name')[0]
    except:
        raise Exception('No previous season')
    logger.info('Seasons ' + str(season) + ' previous season is ' + str(previous_season))
    return previous_season

def get_current_season():
    logger.info('Get current season')
    try:
        season = Season.objects.get(current_flag=True)
    except:
        raise Exception('No Current Season set')
    logger.info('Got current season ' + season.name)
    return season

'''
    Takes a Site and a Season object
    Returns the rz1 total for fullpoint reading type for site and season
'''

def get_rz1_full_point_reading(site, season):
    logger.info('Get rz1 full point reading')

    try:
        dates = get_site_season_start_end(site, season)
        reading = Reading.objects.get(site=site, type__name='Full Point', date__range=(dates.period_from, dates.period_to))
    except:
        raise Exception('No valid Full Point Reading for ' + site.name + ' and season ' + season.name)
    logger.info('Got RZ1 Full Point Reading for ' + site.name + ' and season ' + season.name + ' of ' + str(reading.rz1))
    return reading.rz1

'''
    Takes a Site and a Season object
    Returns a SeasonStartEnd object that contains the period from and period to dates for the site in that season
'''

def get_site_season_start_end(site, season):
    logger.info('Get site ' + str(site.name) + ' season ' + str(season.name) + ' start and end')
    dates = None
    try:
        dates = SeasonStartEnd.objects.get(site=site.id, season=season.id)
        logger.info('Season start: ' + str(dates.period_from) + ' Season end: ' + str(dates.period_to))
    except ObjectDoesNotExist:
        logger.warn('No Season Start and End dates')
    return dates

'''
    process_probe_data - Should be able to process data (readings dictionary) from both neutron and diviner probes

    (P)RWIN and (D)iviner file types store data in depthn field, (N)eutron in depthn_count field

    It expects structure of readings as below:

    Key is site_number and date of reading in mm-dd-yyyy
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

def process_probe_data(readings, serial_unique_id, request, type):
    logger.info("*** process_probe_data")

    for key, site_info in readings.items():
        # Firstly we total up each site-dates readings
        totals = {}
        split_key = key.split(",")

        result = [statistics.mean(k) for k in zip(*site_info)]

        # create data object in the way we want
        data = {}
        data['date'] = split_key[1]

        # Site is the primary key of site number so we need to look it up.
        s = Site.objects.get(site_number=split_key[0])
        data['site'] = s.id
        current_user = request.user
        data['created_by'] = current_user.id
        data['serial_number'] = serial_unique_id
        data['type'] = '1'

        for index in range(len(result)):
            # Neutron goes into depthn_count
            if type == 'N':
                data['depth' + str(index + 1) + '_count'] = result[index]
            else:
                data['depth' + str(index + 1)] = result[index]

        if data:
            r = Reading.objects.filter(site=s.id, date=data['date'], type=1)
            host = request.get_host()
            headers = {'contentType': 'application/json'}
            url = 'http://' + host

            # If reading row already exist update otherwise insert
            if r:
                url += '/api/reading/' + str(r[0].id) + '/'
                logger.info("Ready to update:" + url + " data " + str(data))
                r = requests.patch(url, headers=headers, data=data)
            else:
                url += '/api/reading/'
                logger.info("Ready to insert:" + url + " data " + str(data))
                r = requests.post(url, headers=headers, data=data)
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error('request response' + r.text)
                raise Exception(r.text)
            data = {}

    logger.info("Outside of Process Probe Data Loop:")

'''
    Similar to process_probe_data but:
    - Only one reading array


'''

def process_irrigation_data(irrigation, serial_unique_id, request):
    logger.error("*** process_irrigation_data")

    for key, values in irrigation.items():
        split_key = key.split(",")

        # create data object in the way we want
        data = {}
        data['date'] = split_key[1]

        # Site is the primary key of site number so we need to look it up.
        s = Site.objects.get(site_number=split_key[0])
        data['site'] = s.id

        # Set up data values
        current_user = request.user
        data['created_by'] = current_user.id
        data['serial_number'] = serial_unique_id
        data['type'] = '1' # always probe

        # Order of array
        # 0-100 cm (rz1),0-70 cm (rz2),0-45 cm (rz3),Deficit,ProbeDWU (probe_dwu),EstimatedDWU (estimated_dwu),
        # Rain,Meter,Irrigation(L) (irrigation_litres),Irrigation(mm) (irrigation_mms) ,EffRain1 (effective_rain_1),
        # Effective Rainfall (effective_rainfall) ,EffIrr1 (efflrr1),EffIrr2 (efflrr1), Effective Irrigation (effective_irrigation)
        data['rz1'] = values[0]
        data['rz2'] = values[1]
        data['rz3'] = values[2]
        data['deficit'] = values[3]
        data['probe_dwu'] = values[4]
        data['estimated_dwu'] = values[5]
        data['rain'] = values[6]
        data['meter'] = values[7]
        data['irrigation_litres'] = values[8]
        data['irrigation_mms'] = values[9]
        data['effective_rain_1'] = values[10]
        data['effective_rainfall'] = values[11]
        data['efflrr1'] = values[12]
        data['efflrr2'] = values[13]
        data['effective_irrigation'] = values[14]

        if data:
            # If reading row already exist update otherwise insert
            r = Reading.objects.filter(site=s.id, date=data['date'], type=1)
            host = request.get_host()
            headers = {'contentType': 'application/json'}
            url = 'http://' + host
            # Site, date and type are unique so either get one record or none
            if r:
                url += '/api/reading/' + str(r[0].id) + '/'
                logger.error("Ready to update:" + url + " data " + str(data))
                r = requests.patch(url, headers=headers, data=data)
            else:
                url += '/api/reading/'
                logger.error("Ready to insert:" + url + " data " + str(data))
                r = requests.post(url, headers=headers, data=data)

            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error('request response' + r.text)
                raise Exception(r.text)
            data = {}

    logger.error("Outside of process_irrigation_data Loop:")
