import requests
from requests.auth import HTTPBasicAuth
import json
import statistics
from django.core.exceptions import ObjectDoesNotExist

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site, Reading, ReadingType, Season, SeasonStartEnd, Probe

'''
    Takes a site_id
    Returns a String Title Composing 'FarmName - SiteName (TechnicanFullName)'
'''

def get_title(site_id):
    try:
        s = Site.objects.select_related('technician').select_related('farm').get(id=site_id)
        f = s.farm
        u = s.technician
    except:
        raise Exception('No Site for Title')
    title = str(f.name) + ' - ' + str(s.name) + ' (' + u.first_name + ' ' + u.last_name + ')'
    logger.info('get_title() ' + title)
    return title

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
        raise Exception('No Season Start and End dates for site ' + str(site.name) + ' and season ' + str(season.name))
    return dates

'''
    process_probe_data - Should be able to process data (readings dictionary) from both neutron and diviner probes

    (P)RWIN and (D)iviner file types store data in depthn field, (N)eutron in depthn_count field

    It expects structure of readings as below:

    Key is site_number, date of reading in mm-dd-yyyy, (Probe), (Full Point) or (Refill)
    data = {
        '3306,28-5-2019,Probe' : [
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
        # Away to average out the results
        result = [statistics.mean(k) for k in zip(*site_info)]

        # Need to get objects for keys of reading (date, site, type, probe)
        split_key = key.split(",")
        date = split_key[1]
        reading_type_name = str(split_key[2])
        site_number = split_key[0]

        reading_type = ReadingType.objects.get(name=reading_type_name)
        site = Site.objects.get(site_number=site_number)
        probe = Probe.objects.get(pk=serial_unique_id)

        # Create a data dictionary
        data = {}
        data["date"] = date
        data["type"] = reading_type
        data["created_by"] = request.user
        data["serial_number"] = probe

        for index in range(len(result)):
            # Neutron goes into depthn_count
            if type == 'N':
                data['depth' + str(index + 1) + '_count'] = result[index]
            else:
                data['depth' + str(index + 1)] = result[index]

        if data:
            reading, created = Reading.objects.update_or_create(site=site, date=date, type=reading_type,
                defaults=data)
            data = {} # reset

    logger.info("Outside of Process Probe Data Loop:")

'''
    Similar to process_probe_data but:
    - Only one reading array
'''

def process_irrigation_data(irrigation, serial_unique_id, request):
    logger.error("*** process_irrigation_data")

    for key, values in irrigation.items():
        split_key = key.split(",")

        # Need to get objects for keys of reading (date, site, type, probe)
        split_key = key.split(",")
        date = split_key[1]
        reading_type_name = str(split_key[2])
        site_number = split_key[0]

        reading_type = ReadingType.objects.get(name=reading_type_name)
        site = Site.objects.get(site_number=site_number)
        probe = Probe.objects.get(pk=serial_unique_id)

        # Create a data dictionary
        data = {}
        data["date"] = date
        data["type"] = reading_type
        data["created_by"] = request.user
        data["serial_number"] = probe

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
            reading, created = Reading.objects.update_or_create(site=site, date=date, type=reading_type,
                defaults=data)
            data = {} # reset

    logger.error("Outside of process_irrigation_data Loop:")
