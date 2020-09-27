from django.test import TestCase
from skeleton.models import Reading, Site, ReadingType
from django.core import management
from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class ProcessTest(TestCase):
    fixtures = ['test_processes.json']

    def testSitePinot(self):
        # Get All Pinots Readings for the current season
        season = get_current_season()
        site = Site.objects.get(id=1)
        dates = get_site_season_start_end(site, season)
        readings = Reading.objects.filter(site=site, date__range=(dates.period_from, dates.period_to))

        self.assertEquals(site.name, 'Pinot Noir Springstone')
        # There are 7 readings including Full Point and Refill
        self.assertEquals(readings.count(), 7)

    def testProcesses(self):

        management.call_command('processrootzones')
        management.call_command('processdailywateruse')
        management.call_command('processmeter')
        management.call_command('processrainirrigation')

        season = get_current_season()
        site = Site.objects.get(id=1)
        dates = get_site_season_start_end(site, season)
        readings = Reading.objects.filter(site=site, date__range=(dates.period_from, dates.period_to))

        for reading in readings:
            logger.debug(str(reading))
            if str(reading.date) == '2018-12-14':
                self.assertEquals(reading.rz1, 224)
                self.assertEquals(reading.rz2, 147)
                self.assertEquals(reading.rz3, 82)
                self.assertEquals(reading.deficit, -4)
                self.assertEquals(reading.probe_dwu, None)
                self.assertEquals(reading.estimated_dwu, 9.6)
                self.assertEquals(reading.irrigation_litres, None)
                self.assertEquals(reading.irrigation_mms, None)
                self.assertEquals(reading.effective_rainfall, None)
                self.assertEquals(reading.effective_irrigation, None)
            if str(reading.date) == '2019-05-02':
                self.assertEquals(reading.rz1, 321)
                self.assertEquals(reading.rz2, 178)
                self.assertEquals(reading.rz3, 76)
                self.assertEquals(reading.deficit, -101)
                self.assertEquals(reading.probe_dwu, -0.7)
                self.assertEquals(reading.estimated_dwu, 4.13)
                self.assertEquals(reading.irrigation_litres, 1.33)
                self.assertEquals(reading.irrigation_mms, 0.11)
                self.assertEquals(reading.effective_rainfall, 0.0)
                self.assertEquals(reading.effective_irrigation, 0.11)
            if str(reading.date) == '2019-05-07':
                self.assertEquals(reading.rz1, 314)
                self.assertEquals(reading.rz2, 223)
                self.assertEquals(reading.rz3, 132)
                self.assertEquals(reading.deficit, -94)
                self.assertEquals(reading.probe_dwu, 1.4)
                self.assertEquals(reading.estimated_dwu, 3.87)
                self.assertEquals(reading.irrigation_litres, 0.33)
                self.assertEquals(reading.irrigation_mms, 0.03)
                self.assertEquals(reading.effective_rainfall, 0.0)
                self.assertEquals(reading.effective_irrigation, 0.0)
            if str(reading.date) == '2019-05-14':
                self.assertEquals(reading.rz1, 220)
                self.assertEquals(reading.rz2, 145)
                self.assertEquals(reading.rz3, 82)
                self.assertEquals(reading.deficit, 0)
                self.assertEquals(reading.probe_dwu, 13.43)
                self.assertEquals(reading.estimated_dwu, 4.88)
                self.assertEquals(reading.irrigation_litres, 5)
                self.assertEquals(reading.irrigation_mms, 0.4)
                self.assertEquals(reading.effective_rainfall, 0)
                self.assertEquals(reading.effective_irrigation, 0)
            if str(reading.date) == '2019-05-21':
                self.assertEquals(reading.rz1, 205)
                self.assertEquals(reading.rz2, 144)
                self.assertEquals(reading.rz3, 82)
                self.assertEquals(reading.deficit, 15)
                self.assertEquals(reading.probe_dwu, 2.14)
                self.assertEquals(reading.estimated_dwu, 4.41)
                self.assertEquals(reading.irrigation_litres, 8.33)
                self.assertEquals(reading.irrigation_mms, 0.67)
                self.assertEquals(reading.effective_rainfall, 0.7)
                self.assertEquals(reading.effective_irrigation, 0.67)
'''
    def testDailyWaterUse(self):
        logger.debug('Running daily water use.')


        season = get_current_season()
        site = Site.objects.get(id=1)
        dates = get_site_season_start_end(site, season)
        readings = Reading.objects.filter(site=site, date__range=(dates.period_from, dates.period_to))

        for reading in readings:
            if str(reading.date) == '2018-12-14':

            if str(reading.date) == '2019-05-02':

            if str(reading.date) == '2019-05-07':

            if str(reading.date) == '2019-05-14':

            if str(reading.date) == '2019-05-21':

'''
