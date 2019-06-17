from django.db import models
from django.contrib.auth.models import User

#user = User.objects.get(username='test')
#User.objects.create_superuser(username='test', password='test', email='mabznz@gmail.com')

#ID,FARMNUMBER,FARMNAME,FarmOwner,Comment,Address1,Address2,Town,State,PostCode,Country,Tel,Tel2,Fax,Mobile,Email,FARMREPORT,Folder,FLATITUDE,FLONGITUDE,MapFile,RegionID,UserName,Password
class Farm(models.Model):
    name = models.CharField(max_length=100, null=True)
    owner = models.CharField(max_length=100, null=True)
    comment = models.CharField(max_length=200, null=True)
    address1 = models.CharField(max_length=100, null=True)
    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class Crop(models.Model):
    name = models.CharField(max_length=100, null=True)
    area = models.IntegerField(default=0, null=True)
    position = models.IntegerField(default=0, null=True)
    water_time = models.FloatField(default=0, null=True)
    water_volume = models.FloatField(default=0, null=True)
    depths = models.CharField(max_length=100, null=True)
    horizons = models.CharField(max_length=100, null=True)
    options = models.CharField(max_length=100, null=True)
    zones = models.CharField(max_length=100, null=True)

    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

# link to type of FARMREPORT

class Site(models.Model):
    # Main
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    #?? selected
    name = models.CharField(max_length=100, null=True)
    variety = models.CharField(max_length=100, null=True)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    # Group report # id
    season_start = models.DateTimeField(null=True)
    season_end = models.DateTimeField(null=True)
    #?? bud_break
    #?? cd2 = models.DateTimeField(null=True)
    #?? cd3 = models.DateTimeField(null=True)
    #?? cd4 = models.DateTimeField(null=True)
    #?? cd5 = models.DateTimeField(null=True)
    #?? cd6 = models.DateTimeField(null=True)

    # Irrigations
    irrigation_drip = models.BooleanField(null=True)
    irrigation_area = models.FloatField(default=0, null=True)
    irrigation_time = models.FloatField(default=0, null=True)
    irrigation_delivered_volume = models.FloatField(default=0, null=True)
    irrigation_position = models.FloatField(default=0, null=True)
    irrigation_yield = models.FloatField(default=0, null=True)
    irrigation_allocation_volume = models.FloatField(default=0, null=True)
    # Equivalent depth and delivery rates are derived from above

    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


#Site ID,Selected,Date,Type,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,SN,RZ1,RZ2,RZ3,DEFICIT,PDWU,EDWU,k1,k2,k3,k4,k5,k6,k7,k8,k9,k10,k11,k12,k13,k14,k15,k16,Comment3
class Reading(models.Model):
    # Preseume id is site
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    probe_date = models.DateTimeField()
