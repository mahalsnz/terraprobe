from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

import datetime

IRRIGATION_METHOD = (
    (0, "Non-Drip (Overhead)"),
    (1, "Drip")
)

class Report(models.Model):
    name = models.CharField(max_length=100, null=False)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.name

#ID,FARMNUMBER,FARMNAME,FarmOwner,Comment,Address1,Address2,Town,State,PostCode,Country,Tel,Tel2,Fax,Mobile,Email,FARMREPORT,Folder,FLATITUDE,FLONGITUDE,MapFile,RegionID,UserName,Password
class Farm(models.Model):
    name = models.CharField(max_length=100, null=False)
    owner = models.CharField(max_length=100, null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)

    address = models.ForeignKey('address.Address', null=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)

    #Telephones
    landline = models.CharField(max_length=40, null=True)
    mobile = models.CharField(max_length=40, null=True)
    #Web
    email = models.EmailField(null=True)
    folder = models.CharField(max_length=100, null=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name

class Crop(models.Model):
    # Main
    name = models.CharField(max_length=100, null=True)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)
    dwu_formaula = models.CharField(max_length=100, null=True, blank=True)
    season_start = models.DateField(null=True, blank=True)
    critical_label1 = models.CharField(max_length=100, null=True, blank=True)
    critical_label2 = models.CharField(max_length=100, null=True, blank=True)
    critical_label3 = models.CharField(max_length=100, null=True, blank=True)
    critical_label4 = models.CharField(max_length=100, null=True, blank=True)
    critical_label5 = models.CharField(max_length=100, null=True, blank=True)
    critical_label6 = models.CharField(max_length=100, null=True, blank=True)
    critical_date1 = models.DateField(null=True, blank=True)
    critical_date2 = models.DateField(null=True, blank=True)
    critical_date3 = models.DateField(null=True, blank=True)
    critical_date4 = models.DateField(null=True, blank=True)
    critical_date5 = models.DateField(null=True, blank=True)
    critical_date6 = models.DateField(null=True, blank=True)
    season_end = models.DateField(null=True, blank=True)

    # irrigations
    irrigation_method = models.IntegerField(choices=IRRIGATION_METHOD, default=1) # Drip
    irrigation_area = models.FloatField(null=True, blank=True)
    irrigation_time = models.FloatField(null=True, blank=True)
    irrigation_delivered_volume = models.FloatField(null=True, blank=True)
    irrigation_position = models.FloatField(null=True, blank=True, verbose_name="Monitoring position in")

    irrigation_upper = models.CharField(max_length=200, null=True, blank=True)
    irrigation_lower = models.CharField(max_length=200, null=True, blank=True)
    irrigation_crop_factor = models.IntegerField(null=True, blank=True)
    irrigation_deliver_factor = models.IntegerField(null=True, blank=True)
    irrigation_yield = models.IntegerField(null=True, blank=True)

    irrigation_drip_days = models.IntegerField(null=True, blank=True)
    irrigation_row_space = models.IntegerField(null=True, blank=True)
    irrigation_emit_space = models.IntegerField(null=True, blank=True)
    irrigation_plant_space = models.IntegerField(null=True, blank=True)
    irrigation_wet_width = models.IntegerField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name

class Site(models.Model):
    # Main
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    selected = models.BooleanField(null=True) #???
    name = models.CharField(max_length=100, null=True)
    variety = models.CharField(max_length=100, null=True)
    crop = models.ForeignKey(Crop, null=True, blank=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE)
    season_start = models.DateField(null=True, blank=True)
    bud_break = models.DateField(null=True, blank=True)
    cd2 = models.DateField(null=True, blank=True)
    cd3 = models.DateField(null=True, blank=True)
    cd4 = models.DateField(null=True, blank=True)
    cd5 = models.DateField(null=True, blank=True)
    cd6 = models.DateField(null=True, blank=True)
    season_end = models.DateField(null=True, blank=True)

    # Irrigations
    irrigation_method = models.IntegerField(choices=IRRIGATION_METHOD, default=1) # Drip
    irrigation_area = models.FloatField(null=True, blank=True)
    irrigation_time = models.FloatField(null=True, blank=True)
    irrigation_delivered_volume = models.FloatField(null=True, blank=True)
    irrigation_position = models.FloatField(null=True, blank=True)
    irrigation_yield = models.FloatField(null=True, blank=True)
    irrigation_allocation_volume = models.FloatField(null=True, blank=True)
    # Equivalent depth and delivery rates are derived from above

    # Irrigarions and rain in

    # Root Zone
    rz1_top = models.IntegerField(null=True, blank=True)
    rz1_bottom = models.IntegerField(null=True, blank=True)
    rz2_top = models.IntegerField(null=True, blank=True)
    rz2_bottom = models.IntegerField(null=True, blank=True)
    rz3_top = models.IntegerField(null=True, blank=True)
    rz3_bottom = models.IntegerField(null=True, blank=True)

    # depth
    depth1 = models.IntegerField(null=True, blank=True)
    depth2 = models.IntegerField(null=True, blank=True)
    depth3 = models.IntegerField(null=True, blank=True)
    depth4 = models.IntegerField(null=True, blank=True)
    depth5 = models.IntegerField(null=True, blank=True)
    depth6 = models.IntegerField(null=True, blank=True)
    depth7 = models.IntegerField(null=True, blank=True)
    depth8 = models.IntegerField(null=True, blank=True)
    depth9 = models.IntegerField(null=True, blank=True)
    depth10 = models.IntegerField(null=True, blank=True)
    depth11 = models.IntegerField(null=True, blank=True)
    depth12 = models.IntegerField(null=True, blank=True)

    # Horison Equation
    depth_he1 = models.IntegerField(null=True, blank=True)
    depth_he2 = models.IntegerField(null=True, blank=True)
    depth_he3 = models.IntegerField(null=True, blank=True)
    depth_he4 = models.IntegerField(null=True, blank=True)
    depth_he5 = models.IntegerField(null=True, blank=True)
    depth_he6 = models.IntegerField(null=True, blank=True)
    depth_he7 = models.IntegerField(null=True, blank=True)
    depth_he8 = models.IntegerField(null=True, blank=True)
    depth_he9 = models.IntegerField(null=True, blank=True)
    depth_he10 = models.IntegerField(null=True, blank=True)
    depth_he11 = models.IntegerField(null=True, blank=True)
    depth_he12 = models.IntegerField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

    def __str__(self):
        return self.name


#Site ID,Selected,Date,Type,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,SN,RZ1,RZ2,RZ3,DEFICIT,PDWU,EDWU,k1,k2,k3,k4,k5,k6,k7,k8,k9,k10,k11,k12,k13,k14,k15,k16,Comment3
class Reading(models.Model):
    # Preseume id is site
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, null=False)

    depth1 = models.FloatField(null=True, blank=True)
    depth2 = models.FloatField(null=True, blank=True)
    depth3 = models.FloatField(null=True, blank=True)
    depth4 = models.FloatField(null=True, blank=True)
    depth5 = models.FloatField(null=True, blank=True)
    depth6 = models.FloatField(null=True, blank=True)
    depth7 = models.FloatField(null=True, blank=True)
    depth8 = models.FloatField(null=True, blank=True)
    depth9 = models.FloatField(null=True, blank=True)
    depth10 = models.FloatField(null=True, blank=True)
    depth11 = models.FloatField(null=True, blank=True)
    depth12 = models.FloatField(null=True, blank=True)

    probe_dwu = models.FloatField(null=True, blank=True)
    estimated_dwu = models.FloatField(null=True, blank=True)

    # These are keydata columns from PRWIN being 'hard coded' into readings table instead of being configurable with formulas
    rain = models.FloatField(null=True, blank=True)
    meter = models.FloatField(null=True, blank=True)
    irrigation_litres = models.FloatField(null=True, blank=True)
    irrigation_mms = models.FloatField(null=True, blank=True)
    effective_rain_1 = models.FloatField(null=True, blank=True)
    effective_rainfall = models.FloatField(null=True, blank=True)
    efflrr1 = models.FloatField(null=True, blank=True)
    efflrr2 = models.FloatField(null=True, blank=True)
    effective_irrigation = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User)

class Calibration(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    serial_number = models.IntegerField(default=0, null=True)
    soil_type = models.IntegerField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    intercept = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField('date published', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=User)

    def __str__(self):
        return self.serial_number
