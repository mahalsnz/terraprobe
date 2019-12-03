import requests
import statistics

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site, Reading

def calculate_reading_meter(meter, previous_meter):
    logger.info('Calculating meter reading')

def calculate_irrigation_litres():
    logger.info('Calculating irrigation litres')

def calculate_irrigation_mms():
    logger.info('Calculating irrigation mms')

'''
    process_probe_data - Should be able to process data (readings dictionary) from both neutron and diviner probes

    It expects structure of readings as below

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

def process_probe_data(readings, serial_unique_id, request):
    logger.error("*** process_probe_data")

    for key, site_info in readings.items():
        # Firstly we total up each site-dates readings
        totals = {}
        split_key = key.split(",")

        result = [statistics.mean(k) for k in zip(*site_info)]
        print(str(result))

        # Thirdly we reverse thate order of averaged_totals
        #averaged_totals.reverse()
        #print(averaged_totals)

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
            data['depth' + str(index + 1)] = result[index]

        if data:
            r = Reading.objects.filter(site=s.id, date=data['date'], type=1)
            host = request.get_host()
            headers = {'contentType': 'application/json'}
            url = 'http://' + host
            logger.error("r: " + str(r))
            # If reading row already exist update otherwise insert
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

    logger.error("Outside of Process Probe Data Loop:")

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
