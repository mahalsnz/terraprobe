import requests

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .models import Site

'''
    process_probe_data - Should be able to process data (readings dictionary) from both netron and diviner probes
'''

def process_probe_data(readings, serial_unique_id, request):

    for key, site_info in readings.items():
        # Firstly we total up each site-dates readings
        totals = {}
        split_key = key.split(",")

        for depth_arr in site_info:
            for index in range(len(depth_arr)):
                print("Index:" + str(index))
                print(depth_arr[index])
                if index in totals:
                    totals[index] = int(totals[index]) + int(depth_arr[index])
                else:
                    totals[index] = int(depth_arr[index])
        # We don't store zeros, bad reading
        #if int(reading_line[6]) > 0:
        # Secondly we average out each reading from the amount of readings taken
        averaged_totals = []
        #readings_taken = len(site_info)

        for key, value in totals.items():
            print("key:" + str(key) + "value:" + str(value) + " readings_count:" + str(readings_count))
            if int(value) > 0:
                readings_count = readings_count + 1
                averaged_totals.append(int(value) / readings_count)

        # Thirdly we reverse thate order of averaged_totals
        averaged_totals.reverse()
        print(averaged_totals)

        # create data object in the way we want
        data = {}
        data['date'] = split_key[1]

        # Site is the primary key of site number so we need to look it up.
        s = Site.objects.get(site_number=split_key[0])
        data['site'] = s.id

        # TODO: When we have authorization over site set up can have logged in user as created by
        data['created_by'] = '2'

        data['serial_number'] = serial_unique_id
        data['type'] = '1' # always probe

        for index in range(len(averaged_totals)):
            data['depth' + str(index + 1)] = averaged_totals[index]

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

    logger.error("Outside of Process Data Loop:")
