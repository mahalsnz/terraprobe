from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Q
from django.urls import reverse

import datetime

# Helpers

ALL_CHOICE = (
    ("0", "All" )
)

IRRIGATION_METHOD = (
    (0, "Non-Drip (Overhead)"),
    (1, "Drip")
)

DEPTH_VALUES = (
    (0, 0),
    (10, 10),
    (20, 20),
    (30, 30),
    (40, 40),
    (50, 50),
    (60, 60),
    (70, 70),
    (80, 80),
    (90, 90),
    (100, 100),
    (110, 110),
    (120, 120),
)

DEPTH_HE_VALUES = (
    (0, 0),
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (9, 9),
    (10, 10)
)

class UserFullName(User):
    class Meta:
        proxy = True

    def __str__(self):
        return self.get_full_name()

# Database

class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')

class ReadingType(models.Model):
    name = models.CharField(max_length=100, null=False)
    comment = models.CharField(max_length=200, null=True, blank=True)
    formula = models.CharField(max_length=200, null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.name

class Report(models.Model):
    name = models.CharField(max_length=100, null=False)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.name

class Season(models.Model):
    name = models.CharField(max_length=20, null=False)
    season_date = models.DateField(default=timezone.now, null=True, help_text='The Year to create a new season. For a season spanning two years is must be the starting year. ')
    current_flag = models.BooleanField(default=None, null=True, help_text="Is this the current season, only one season can be the current season")
    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    @property
    def formatted_season_start_year(self):
        return self.season_date.strftime('%Y')

    def __str__(self):
        return self.name

class WeatherStation(models.Model):
    region = models.ForeignKey('address.State', null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True)
    code = models.CharField(max_length=4, null=True)

    def __str__(self):
        return self.name

class CriticalDateType(models.Model):
    name = models.CharField(max_length=50, null=False)
    season_flag = models.BooleanField()
    comment = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.name

class Farm(models.Model):
    name = models.CharField(max_length=100, null=False)
    owner = models.CharField(max_length=100, null=False, default="TEST")

    comment = models.CharField(max_length=200, null=True, blank=True)

    address = models.ForeignKey('address.Address', null=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)
    weatherstation = models.ForeignKey(WeatherStation, null=True, blank=True, on_delete=models.CASCADE)

    #Telephones
    landline = models.CharField(max_length=40, null=True, blank=True)
    mobile = models.CharField(max_length=40, null=True, blank=True)
    #Web
    email = models.EmailField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name

class Variety(models.Model):
    name = models.CharField(max_length=100, null=True)
    comment = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name

class VarietySeasonTemplate(models.Model):
    variety = models.ForeignKey(Variety, null=False, on_delete=models.CASCADE)
    critical_date_type = models.ForeignKey(CriticalDateType, null=False, on_delete=models.CASCADE, help_text='The Critical Date Type to create new season Critical Dates for all sites that are of this variety.')
    season_date = models.DateField(default=timezone.now, null=False, help_text='The day and month to create new season Critical Dates for all sites that are of this variety.')

    comment = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return str(self.variety) + ' - ' + str(self.critical_date_type) + ' - ' + str(self.season_date.strftime('%B-%d'))

    @property
    def formatted_variety_season_date(self):
        return self.season_date.strftime('%B-%d')

class Crop(models.Model):
    name = models.CharField(max_length=100, null=False, default='Crop')
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)
    dwu_formaula = models.CharField(max_length=100, null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name

class Product(models.Model):
    crop = models.ForeignKey(Crop, null=False, on_delete=models.CASCADE)
    variety = models.ForeignKey(Variety, null=False, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return str(self.crop) + ' - ' + str(self.variety)

    class Meta:
        unique_together = (('crop', 'variety'))

class StrategyType(models.Model):
    name = models.CharField(max_length=50, null=False)
    percentage = models.FloatField(null=False, default=0, help_text="A percentage between 0 and 1 indicating the difference that the lower strategy should be below the upper strategy for a site. This is taken from the high limit.")
    comment = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(percentage__gte=0), name='strategy_type_percentage_gte_0'),
            models.CheckConstraint(check=Q(percentage__lte=1), name='strategy_type_percentage_1te_1')
        ]

    def __str__(self):
        return self.name

class Strategy(models.Model):
    type = models.ForeignKey(StrategyType, null=False, on_delete=models.CASCADE)
    critical_date_type = models.ForeignKey(CriticalDateType, null=False, on_delete=models.CASCADE)
    days = models.IntegerField(null=False, default=0, help_text="A positive or negative number indicated the amount of days away from that critical date.")
    percentage = models.FloatField(null=False, default=0, help_text="A percentage between 0 and 1 indicating the variation from the limit associated with the strategy.")
    comment = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(percentage__gte=0), name='strategy_percentage_gte_0'),
            models.CheckConstraint(check=Q(percentage__lte=1), name='strategy_percentage_1te_1')
        ]

    def __str__(self):
        type = str(self.type)
        critical_date_type = str(self.critical_date_type)
        days = str(self.days)
        percentage = str(self.percentage)
        return type + ":" + critical_date_type + ":" + days + ":" + percentage

class Site(models.Model):
    # Main
    site_number = models.CharField(max_length=20, unique=True, null=False)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    technician = models.ForeignKey(User, related_name="technician_id", on_delete=models.CASCADE, default=1)
    selected = models.BooleanField(null=True) #???
    name = models.CharField(max_length=100, null=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)

    # Irrigations
    irrigation_method = models.IntegerField(choices=IRRIGATION_METHOD, default=1, help_text="Are you sure you want to change this to Overhead?") # Drip
    irrigation_area = models.FloatField(null=True, blank=True)
    irrigation_time = models.FloatField(null=True, blank=True)
    irrigation_delivered_volume = models.FloatField(null=True, blank=True)
    irrigation_position = models.FloatField(null=True, blank=True, verbose_name="Inline Water Meter Position in Trees")
    irrigation_yield = models.FloatField(null=True, blank=True)
    irrigation_allocation_volume = models.FloatField(null=True, blank=True)
    # Equivalent depth and delivery rates are derived from above

    # Irrigarions and rain in

    # Root Zone = Top is always 0
    rz1_bottom = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True, help_text="The Bottom Depth of Root Zone 1. The Top will aways be zero.")
    rz2_bottom = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True, help_text="The Bottom Depth of Root Zone 2. The Top will aways be zero.")
    rz3_bottom = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True, help_text="The Bottom Depth of Root Zone 3. The Top will aways be zero.")
    rz_percentage = models.FloatField(null=False, default=1, help_text="A percentage between 0 and 1 indicating total 7 day water use. A lower percentage from 100 indicates a smaller root stock.")

    # depth
    depth1 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth2 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth3 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth4 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth5 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth6 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth7 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth8 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth9 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)
    depth10 = models.IntegerField(choices=DEPTH_VALUES, default=0, null=True, blank=True)

    # Horison Equation
    depth_he1 = models.IntegerField(choices=DEPTH_HE_VALUES, default=1, null=True, blank=True)
    depth_he2 = models.IntegerField(choices=DEPTH_HE_VALUES, default=2, null=True, blank=True)
    depth_he3 = models.IntegerField(choices=DEPTH_HE_VALUES, default=3, null=True, blank=True)
    depth_he4 = models.IntegerField(choices=DEPTH_HE_VALUES, default=4, null=True, blank=True)
    depth_he5 = models.IntegerField(choices=DEPTH_HE_VALUES, default=5, null=True, blank=True)
    depth_he6 = models.IntegerField(choices=DEPTH_HE_VALUES, default=6, null=True, blank=True)
    depth_he7 = models.IntegerField(choices=DEPTH_HE_VALUES, default=7, null=True, blank=True)
    depth_he8 = models.IntegerField(choices=DEPTH_HE_VALUES, default=8, null=True, blank=True)
    depth_he9 = models.IntegerField(choices=DEPTH_HE_VALUES, default=9, null=True, blank=True)
    depth_he10 = models.IntegerField(choices=DEPTH_HE_VALUES, default=10, null=True, blank=True)

    #Scheduling
    upper_limit = models.ForeignKey(ReadingType, related_name="upper_limit_type", null=True, blank=True, on_delete=models.CASCADE, help_text="Target Upper line for Graph")
    lower_limit = models.ForeignKey(ReadingType, related_name="lower_limit_type", null=True, blank=True, on_delete=models.CASCADE, help_text="Target Lower line for Graph")
    strategy = models.ForeignKey(StrategyType, null=True, blank=True, on_delete=models.CASCADE)

    emitter_rate = models.FloatField(null=False, default=1)
    row_spacing = models.FloatField(null=False, default=1, verbose_name="Row Spacing (Meters)")
    emitter_spacing = models.FloatField(null=False, default=1, verbose_name="Emitter Spacing (Meters)")
    plant_spacing = models.FloatField(null=False, default=1, verbose_name="Plant Spacing (Meters)")

    comment = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(rz_percentage__gte=0), name='site_rz_percentage_gte_0'),
            models.CheckConstraint(check=Q(rz_percentage__lte=1), name='site_rz_percentage_percentage_1te_1')
        ]

    def __str__(self):
        return self.name

    @property
    def application_rate(self):
        application_rate = self.emitter_rate / (self.row_spacing * self.emitter_spacing)
        return round(application_rate, 2)

# Combines Site name and number. A lot of sites are known by number
class SiteDescription(Site):
    class Meta:
        proxy = True

    def __str__(self):
        return "(" + self.site_number + ") " + self.name

class CriticalDate(models.Model):
    site = models.ForeignKey(SiteDescription, related_name='sites', on_delete=models.CASCADE)
    season = models.ForeignKey(Season, related_name='seasons', on_delete=models.CASCADE)
    type = models.ForeignKey(CriticalDateType, related_name='critical_date_types', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, null=False)
    comment = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        date = str(self.date)
        site = str(self.site)
        return site + ":" + date

    class Meta:
        unique_together = (('site', 'season', 'type'))

class SeasonStartEnd(models.Model):
    site = models.ForeignKey(SiteDescription, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, primary_key=True, on_delete=models.CASCADE)
    start = models.ForeignKey(CriticalDateType, related_name='start_date_type', on_delete=models.CASCADE)
    end = models.ForeignKey(CriticalDateType, related_name='end_date_type', on_delete=models.CASCADE)
    season_name = models.CharField(max_length=20)
    site_name = models.CharField(max_length=100)
    season_current_flag = models.BooleanField()
    period_from = models.DateField()
    period_to = models.DateField()

    class Meta:
        managed = False
        db_table = "skeleton_season_start_end"
        unique_together = (('site', 'season'),)

class Diviner(models.Model):
    diviner_number = models.CharField(max_length=50, null=False)
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.CASCADE)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.diviner_number

class Probe(models.Model):
    serial_number = models.CharField(max_length=100, null=False, default="Manual")
    comment = models.CharField(max_length=200, null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.serial_number

class ProbeDiviner(models.Model):
    probe = models.ForeignKey(Probe, null=False, on_delete=models.CASCADE)
    diviner = models.ForeignKey(Diviner, null=False, blank=True, on_delete=models.CASCADE)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def get_absolute_url(self):
        return reverse('probe_diviner_detail', args=[str(self.id)])

    def __str__(self):
        return str(self.probe) + ":" + str(self.diviner)

class Calibration(models.Model):
    serial_number = models.ForeignKey(Probe, null=True, blank=True, on_delete=models.CASCADE)
    soil_type = models.IntegerField(choices=DEPTH_HE_VALUES, default=1, null=True, blank=True)
    period_from = models.DateField(default=timezone.now, null=False)
    period_to = models.DateField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    intercept = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        serial_text = str(self.serial_number.serial_number)
        soil_type_text = str(self.soil_type)
        period_from_text = str(self.period_from)
        return serial_text + ":" + soil_type_text + ":" + period_from_text

#Site ID,Selected,Date,Type,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,SN,RZ1,RZ2,RZ3,DEFICIT,PDWU,EDWU,k1,k2,k3,k4,k5,k6,k7,k8,k9,k10,k11,k12,k13,k14,k15,k16,Comment3
class Reading(models.Model):
    # Preseume id is site
    site = models.ForeignKey(Site, related_name='readings', null=False, on_delete=models.CASCADE)
    type = models.ForeignKey(ReadingType, null=False, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, null=False)

    reviewed = models.BooleanField(default=False, null=True, help_text="Has reading been reviewed. Only really applies to Probe readings.")

    depth1 = models.FloatField(null=True, blank=True, verbose_name="Depth1 VSW/Normal")
    depth2 = models.FloatField(null=True, blank=True, verbose_name="Depth1 VSW/Normal")
    depth3 = models.FloatField(null=True, blank=True, verbose_name="Depth3 VSW/Normal")
    depth4 = models.FloatField(null=True, blank=True, verbose_name="Depth4 VSW/Normal")
    depth5 = models.FloatField(null=True, blank=True, verbose_name="Depth5 VSW/Normal")
    depth6 = models.FloatField(null=True, blank=True, verbose_name="Depth6 VSW/Normal")
    depth7 = models.FloatField(null=True, blank=True, verbose_name="Depth7 VSW/Normal")
    depth8 = models.FloatField(null=True, blank=True, verbose_name="Depth8 VSW/Normal")
    depth9 = models.FloatField(null=True, blank=True, verbose_name="Depth9 VSW/Normal")
    depth10 = models.FloatField(null=True, blank=True, verbose_name="Depth10 VSW/Normal")

    depth1_count = models.FloatField(null=True, blank=True)
    depth2_count = models.FloatField(null=True, blank=True)
    depth3_count = models.FloatField(null=True, blank=True)
    depth4_count = models.FloatField(null=True, blank=True)
    depth5_count = models.FloatField(null=True, blank=True)
    depth6_count = models.FloatField(null=True, blank=True)
    depth7_count = models.FloatField(null=True, blank=True)
    depth8_count = models.FloatField(null=True, blank=True)
    depth9_count = models.FloatField(null=True, blank=True)
    depth10_count = models.FloatField(null=True, blank=True)

    serial_number = models.ForeignKey(Probe, null=True,  blank=True, on_delete=models.CASCADE)

    rz1 = models.FloatField(null=True, blank=True, verbose_name="Root Zone 1")
    rz2 = models.FloatField(null=True, blank=True, verbose_name="Root Zone 2")
    rz3 = models.FloatField(null=True, blank=True, verbose_name="Root Zone 3")
    deficit = models.FloatField(null=True, blank=True, help_text="Deficit is the difference between the full point reading and root zone 1")
    probe_dwu = models.FloatField(null=True, blank=True, verbose_name="Probe Daily Water Use", help_text="PDWU is the rate of change of the water content of root zone 1, expressed in mm/day")
    estimated_dwu = models.FloatField(null=True, blank=True, verbose_name="Estimated Daily Water Use", help_text="EDWU is KC Reading for crop multiplied by ET reading for region")

    # These are keydata columns from PRWIN being 'hard coded' into readings table instead of being configurable with formulas
    rain = models.FloatField(null=True, blank=True, help_text="Rainfall reding")
    meter = models.FloatField(null=True, blank=True, verbose_name="Inline Water Meter in Litres", help_text="Meter reading")
    irrigation_litres = models.FloatField(null=True, blank=True, verbose_name="Irrigation in Litres", help_text="Difference in Meter readings multipled by the Irrigation Postion")
    irrigation_mms = models.FloatField(null=True, blank=True, verbose_name="Irrigation in Millimetres", help_text="Irrigation in Litres divided by Schedule Rowspace and Schedule Plantspace divided by 10000")
    effective_rain_1 = models.FloatField(null=True, blank=True, help_text="keydata 5 - Well Complicated")
    effective_rainfall = models.FloatField(null=True, blank=True, help_text="keydata 6")
    efflrr1 = models.FloatField(null=True, blank=True, help_text="keydata 7")
    efflrr2 = models.FloatField(null=True, blank=True, help_text="keydata 8")
    effective_irrigation = models.FloatField(null=True, blank=True, help_text="keydata 9")

    comment = models.TextField(null=True, blank=True)
    # list(calendar.day_abbr) ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    rec_Mon = models.FloatField(null=True, blank=True, default=0)
    rec_Tue = models.FloatField(null=True, blank=True, default=0)
    rec_Wed = models.FloatField(null=True, blank=True, default=0)
    rec_Thu = models.FloatField(null=True, blank=True, default=0)
    rec_Fri = models.FloatField(null=True, blank=True, default=0)
    rec_Sat = models.FloatField(null=True, blank=True, default=0)
    rec_Sun = models.FloatField(null=True, blank=True, default=0)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        site_text = self.site.name
        return site_text + ':' + self.date.strftime('%Y-%m-%d')

    class Meta:
        unique_together = (('date', 'site', 'type'))
        get_latest_by = 'date'

'''
These are crop coefficients (Kc) from .DWU files are daily water use data.
The CSV files are:

Day, crop KC

Apples for example - season start is day 0 at a kc of 0.5
This remains until day 31 when the KC changes to 1.0
etc, etc
The number 283 at the start is the beginning day of the season (~Oct 11th)

Grapes.kc is the same different date format.
It uses the Critical dates (CD) +- days to determine when the kc changes.
'''

class KCReading(models.Model):
    crop = models.ForeignKey(Crop, null=False, on_delete=models.CASCADE)
    period_from = models.DateField(default=timezone.now, null=False)
    period_to = models.DateField(default=timezone.now, null=False)
    kc = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        crop_text = str(self.crop)
        period_from_text = str(self.period_from)
        period_to_text = str(self.period_to)
        kc_text = str(self.kc)
        return crop_text + ":" + period_from_text + ":" + period_to_text + ":" + kc_text

'''
The ET data comes via Hortplus as a daily ET based on a refrence crop (grass)

The ET data from the reference crop is then multiplied by the crop KC (Is different for differnt crops. Have attached 3 examples)
'''

class ETReading(models.Model):
    state = models.ForeignKey('address.State', null=False, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, null=False)
    weekly = models.FloatField(null=True, blank=True)
    daily = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        state_text = str(self.state)
        date_text = str(self.date)
        daily_text = str(self.daily)
        return state_text  + ":" + date_text + ":" + daily_text
