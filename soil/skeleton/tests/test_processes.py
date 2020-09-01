from django.test import TestCase
from skeleton.models import Reading, Site, ReadingType
from django.core import management
from skeleton.utils import get_current_season, get_site_season_start_end

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

class ProcessTest(TestCase):
    fixtures = ['test_processes.json']

    # Test we have loaded correct data
    def testSitePinot(self):
        site = Site.objects.get(id=1)
        self.assertEquals(site.name, 'Pinot Noir Springstone')

    def testRootZones(self):
        management.call_command('processrootzones')

        # Get All Pinots Readings for the current season
        season = get_current_season()
        site = Site.objects.get(id=1)
        dates = get_site_season_start_end(site, season)
        readings = Reading.objects.filter(site=site, date__range=(dates.period_from, dates.period_to))

        # There are 7 readigns including Full Point and Refill
        self.assertEquals(readings.count(), 7)
        for reading in readings:
            logger.debug(str(reading))
            if str(reading.date) == '2018-12-14':
                self.assertEquals(reading.rz1, 224)
                self.assertEquals(reading.rz2, 147)
                self.assertEquals(reading.rz3, 82)
            if str(reading.date) == '2019-05-02':
                self.assertEquals(reading.rz1, 321)
                self.assertEquals(reading.rz2, 178)
                self.assertEquals(reading.rz3, 76)
            if str(reading.date) == '2019-05-07':
                self.assertEquals(reading.rz1, 314)
                self.assertEquals(reading.rz2, 223)
                self.assertEquals(reading.rz3, 132)
            if str(reading.date) == '2019-05-14':
                self.assertEquals(reading.rz1, 220)
                self.assertEquals(reading.rz2, 145)
                self.assertEquals(reading.rz3, 82)
            if str(reading.date) == '2019-05-21':
                self.assertEquals(reading.rz1, 205)
                self.assertEquals(reading.rz2, 144)
                self.assertEquals(reading.rz3, 82)
