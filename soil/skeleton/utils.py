import requests
import statistics

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site

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
    logger.error(readings)
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
        data['type'] = '1' # always probe

        for index in range(len(result)):
            data['depth' + str(index + 1)] = result[index]

        logger.error("Ready to insert:" + str(data))

        if data:
            # TODO: Add unique key on readings table for date, reading_type and site
            logger.error("Post data if something in data" + str(data))
            host = request.get_host()
            headers = {'contentType': 'application/json'}
            r = requests.post('http://' + host + '/api/reading/', headers=headers, data=data)
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error('request response' + r.text)
                raise Exception(r.text)
            data = {}

    logger.error("Outside of Process Probe Data Loop:")
