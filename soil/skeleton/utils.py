import requests
from requests.auth import HTTPBasicAuth
import json
import numpy as np
import math
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.db.models.functions import Coalesce
from datetime import timedelta

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site, Reading, ReadingType, Season, SeasonStartEnd, Probe, SeasonalSoilStat

"""
    From a full point and refill value calculates and returns a string soil type of heavy, meduim or light
"""

def get_soil_type(full):
    #logger.debug("Full Point" + str(full))

    if full > 270:
        return "HEV"
    elif full < 194:
        return "LIG"
    else:
        return "MED"

def calculate_seasonal_soil_stat():
    seasons = Season.objects.filter()
    seasons_to_calculate = []
    for season in seasons:
        count = SeasonalSoilStat.objects.filter(season=season).count()
        logger.debug("Records for season " + season.name + " is:" + str(count))
        if count != 3:
            logger.debug("Need to calculate seasons " + str(seasons_to_calculate))
            seasons_to_calculate.append(season.id)

    if seasons_to_calculate:
        for season_id in seasons_to_calculate:
            calculate_soil_averages_for_all_sites(season_id)
    else:
        return False

def calculate_soil_averages_for_all_sites(season_id):
    seasons = SeasonStartEnd.objects.filter(season_id=season_id).order_by('period_from')

    # TODO! get each of the three choices for soil type SeasonalSoilStat.objects.filter(
    sites = {}
    sites["HEV"] = []
    sites["MED"] = []
    sites["LIG"] = []

    for season in seasons:
        try:
            full_point = Reading.objects.get(site=season.site_id, type__name="Full Point", date__range=(season.period_from, season.period_to))
            if (full_point.rz1 is None):
                continue
            site_soil_type = get_soil_type(full_point.rz1)
            if site_soil_type == "HEV":
                sites["HEV"].append(season.site_id)
            elif site_soil_type == "MED":
                sites["MED"].append(season.site_id)
            else:
                sites["LIG"].append(season.site_id)
        except ObjectDoesNotExist:
            logger.debug("******ObjectDoesNotExist for site " + season.site_name)
            continue

    logger.debug('Sites to process ' + str(sites))

    for key in sites:
        logger.debug('Soil type ' + str(key))
        total_eff_irrigation = 0
        total_irrigation_mms = 0

        for site_id in sites[key]:
            season = SeasonStartEnd.objects.get(season_id=season_id, site_id=site_id)
            logger.debug('Site ' + str(site_id))

            readings = Reading.objects.filter(site=site_id, type__name="Probe", date__range=(season.period_from, season.period_to)).order_by('date')

            irrigation_mms = readings.aggregate(irrigation_mms__sum=Coalesce(Sum('irrigation_mms'), 0))
            irrigation_mms_sum = irrigation_mms.get('irrigation_mms__sum')

            eff_irrigation = readings.aggregate(effective_irrigation__sum=Coalesce(Sum('effective_irrigation'), 0))
            eff_irrigation_sum = eff_irrigation.get('effective_irrigation__sum')

            total_eff_irrigation += eff_irrigation_sum
            total_irrigation_mms += irrigation_mms_sum

        total_sites = len(sites[key])
        total_eff_irrigation = round(total_eff_irrigation / total_sites)
        logger.debug('Total eff irrigation ' + str(total_eff_irrigation) + ' Total irrigation' + str(total_irrigation_mms) + ' total sites ' +
            str(total_sites))

        total_eff_irrigation_perc = 0

        if total_sites > 0:
            total_eff_irrigation_perc = round(total_eff_irrigation /  round(total_irrigation_mms / total_sites) * 100)

        logger.debug('Total eff irrigation percentage %' + str(total_eff_irrigation_perc))

        SeasonalSoilStat.objects.update_or_create(season=season.season, soil_type=str(key), total_irrigation_mms=total_irrigation_mms,
            total_effective_irrigation=total_eff_irrigation, perc_effective_irrigation=total_eff_irrigation_perc)

"""
    sites = Site.objects.filter(is_active=True)
    sites_to_average = []

    # We want to stretch the period from and to dates out to cover as many sites as we can in that season (These dates start out for a particular site)
    #logger.debug("Before period_to:" + str(period_to))
    period_to = period_to + timedelta(31)
    #logger.debug("After period_to:" + str(period_to))

    #logger.debug("Before period_from:" + str(period_from))
    period_from = period_from + timedelta(-31)
    #logger.debug("After period_from:" + str(period_from))

    for site in sites:
        # Decide first what soil type a site is
        try:
            full_point = Reading.objects.get(site=site.id, type__name="Full Point", date__range=(period_from, period_to))
            refill = Reading.objects.get(site=site.id, type__name="Refill", date__range=(period_from, period_to))

            if ((full_point.rz1 is None) or (refill.rz1 is None)):
                continue

            site_soil_type = get_soil_type(full_point.rz1, refill.rz1)

            # If a match put it in list
            if passed_soil_type == site_soil_type:
                logger.debug("We have a match on soil types for site " + site.name)
                sites_to_average.append(site.id)
            else:
                logger.debug("No match for site " + str(site.site_number))
        except ObjectDoesNotExist:
            logger.debug("****** " + str(site.site_number))
            continue

    # End find of sites

    total_eff_irrigation = 0
    total_irrigation_mms = 0
    for site_id in sites_to_average:
        readings = Reading.objects.filter(site=site_id, type__name="Probe", date__range=(period_from, period_to)).order_by('date')

        irrigation_mms = readings.aggregate(irrigation_mms__sum=Coalesce(Sum('irrigation_mms'), 0))
        irrigation_mms_sum = irrigation_mms.get('irrigation_mms__sum')

        eff_irrigation = readings.aggregate(effective_irrigation__sum=Coalesce(Sum('effective_irrigation'), 0))
        eff_irrigation_sum = eff_irrigation.get('effective_irrigation__sum')

        total_eff_irrigation += eff_irrigation_sum
        total_irrigation_mms += irrigation_mms_sum

    total_sites = len(sites_to_average)
    total_eff_irrigation = round(total_eff_irrigation / total_sites)
    logger.debug('Total eff irrigation ' + str(total_eff_irrigation) + ' Total irrigation' + str(total_irrigation_mms) + ' total sites ' +
        str(total_sites))

    total_eff_irrigation_perc = 0

    if total_sites > 0:
        total_eff_irrigation_perc = round(total_eff_irrigation /  round(total_irrigation_mms / total_sites) * 100)

    logger.debug('Total eff irrigation percentage %' + str(total_eff_irrigation_perc))
    return (total_eff_irrigation, total_eff_irrigation_perc)
"""
"""
    Accepts a reading object
    Returns the week start abbrivation (MO, TU.....), the week start number and an array of weekly values for the reading
    (week_start_abbr, week_start, week_values) = get_weekly_reading_values(reading)
"""

def get_weekly_reading_values(reading):

    week_start = reading.date.weekday() + 1
    week_start_abbr = calendar.day_abbr[week_start]
    week_values = {}
    day_value = 0
    water_day_value = 0
    for day in list(calendar.day_abbr):
        logger.debug(day)
        day_value = request.GET.get(day)

        logger.debug('request day value:' + str(day_value))
        column = 'rec_' + str(day)
        if day_value:
            setattr(reading, column, day_value)
        day_value = getattr(reading, column)
        if day_value is None:
            day_value = 0
        week_values[day] = day_value

        water_day_value = round(float(site.application_rate) * float(day_value))
        week_values[day + '-water'] = water_day_value
    return (week_start_abbr, week_start, week_values)

class SiteReadingException(Exception):

    """
        Takes a message as well as a Site object

        exaple usage: SiteReadingException("Root Zone 1 is blank for reading on " + str(date), site)
    """

    def __init__(self, message, site):
        self.message = message
        self.site = site
        super().__init__(self.message)

    def __str__(self):
        return f'{self.site.site_number} - {self.site.name} >>> {self.message}'

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
    logger.info('Get site ' + str(site.site_number) + ':'  + str(site.name) + ' season ' + str(season.name) + ' start and end')
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
    sites = []
    for key, site_info in readings.items():
        # get the mean of the readings. Use nanmean as nan used for zeros and we don't want them affecting the mean
        result = [np.nanmean(k) for k in zip(*site_info)]


        # Need to get objects for keys of reading (date, site, type, probe)
        split_key = key.split(",")
        date = split_key[1]
        reading_type_name = str(split_key[2])
        site_number = split_key[0]
        logger.info("Result after working out mean for site_number:" + str(site_number) + '\n' + str(result))
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
            if not math.isnan(result[index]):
                # Neutron goes into depthn_count
                if type == 'N':
                    data['depth' + str(index + 1) + '_count'] = result[index]
                else:
                    data['depth' + str(index + 1)] = result[index]
            else:
                logger.debug("Looks like all nan for depth so not inserting")

        if data:
            reading, created = Reading.objects.update_or_create(site=site, date=date, type=reading_type,
                defaults=data)
            data = {} # reset
            sites.append(site)

    logger.info("Outside of Process Probe Data Loop:")
    return sites

'''
    Similar to process_probe_data but:
    - Only one reading array
'''

def process_irrigation_data(irrigation, serial_unique_id, request):
    logger.info("*** process_irrigation_data")

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

    logger.info("Outside of process_irrigation_data Loop:")

'''
    Get a rootzone mapping for a site
    Returns a Dictionary keyed by siteid and rootzone
    {'6rz1': [
        {'depth': 10, 'he': 1, 'rz_bottom': 60}, {'depth': 20, 'he': 2, 'rz_bottom': 60}, {'depth': 30, 'he': 3, 'rz_bottom': 60}, {'depth': 40, 'he': 4, 'rz_bottom': 60}, {'depth': 50, 'he': 5, 'rz_bottom': 60}, {'depth': 60, 'he': 6, 'rz_bottom': 60}
        ],
     '6rz2': [
        {'depth': 10, 'he': 1, 'rz_bottom': 20}, {'depth': 20, 'he': 2, 'rz_bottom': 20}
        ],
     '6rz3': [
        {'depth': 10, 'he': 1, 'rz_bottom': 40}, {'depth': 20, 'he': 2, 'rz_bottom': 40}, {'depth': 30, 'he': 3, 'rz_bottom': 40}, {'depth': 40, 'he': 4, 'rz_bottom': 40}
        ]
    }

'''

def get_rootzone_mapping(site):
    logger.info("*** get_rootzone_mapping for site " + site.name)

    rootzones = {}
    for z in range(1,4):
        rootzone = 'rz' + str(z)
        key = str(site.id) + rootzone
        logger.debug("Key:" + key)
        depth_array = []
        rootzones[key] = []

        top = 0 # Top of root zone is hard coded to zero
        bottom = getattr(site, rootzone + '_bottom')
        logger.debug("Top:" + str(top) + ' Bottom:' + str(bottom))
        if bottom is not None:
            seen_depth_in_bottom = False
            first_no_depth = False
            first_no_depth_value = 0
            first_no_depth_he = 0
            for i in range(1,11):
                depths_key = {}
                column = 'depth' + str(i)
                depth = getattr(site, column)

                if depth:
                    if depth > top and depth < bottom:
                        logger.debug(column + ' of site:' + str(depth))
                        he = int(getattr(site, 'depth_he' + str(i)))
                        depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom }
                        depth_array.append(depths_key)
                    if bottom == depth:
                        logger.debug(column + ' of site:' + str(depth))
                        logger.debug('Bottom equals a depth figure for this rootzone')
                        he = int(getattr(site, 'depth_he' + str(i)))
                        depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom  }
                        depth_array.append(depths_key)
                        seen_depth_in_bottom = True
                    if not seen_depth_in_bottom and depth > bottom:
                        logger.debug('Depth greater than Bottom and not seen_depth_in_bottom')
                        logger.debug(column + ' of site:' + str(depth))
                        he = int(getattr(site, 'depth_he' + str(i)))
                        depths_key = { 'depth' : depth, 'he' : he, 'rz_bottom' : bottom  }
                        depth_array.append(depths_key)
                        break
                else:
                    logger.debug('No depth for column ' + column)
                    first_no_depth = True

            # We have an exception here where we just add it to the depth_array
            if not seen_depth_in_bottom:
                depths_key = { 'depth' : bottom, 'he' : 0, 'rz_bottom' : bottom  }
                depth_array.append(depths_key)
        rootzones[key] = depth_array
    logger.debug('Return Root Zone ' + str(rootzones))
    logger.info('Finished site root zone map.....')
    return rootzones
