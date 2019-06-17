from django.db import models
from django.contrib.auth.models import User

IRRIGATION_METHOD = (
    (0, "Non-Drip"),
    (1, "Drip")
)

#user = User.objects.get(username='test')
#User.objects.create_superuser(username='test', password='test', email='mabznz@gmail.com')

class Report(models.Model):
    name = models.CharField(max_length=100, null=True)

    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

#ID,FARMNUMBER,FARMNAME,FarmOwner,Comment,Address1,Address2,Town,State,PostCode,Country,Tel,Tel2,Fax,Mobile,Email,FARMREPORT,Folder,FLATITUDE,FLONGITUDE,MapFile,RegionID,UserName,Password
class Farm(models.Model):
    name = models.CharField(max_length=100, null=True)
    owner = models.CharField(max_length=100, null=True)
    comment = models.CharField(max_length=200, null=True)
    #address1 = models.CharField(max_length=100, null=True)
    #address2 = models.CharField(max_length=100, null=True)
    #town = models.CharField(max_length=100, null=True)
    #state = models.CharField(max_length=100, null=True)
    #city = models.CharField(max_length=100, null=True)
    #postcode = models.CharField(max_length=100, null=True)
    #country = models.CharField(max_length=100, null=True)
    #report = models.ForeignKey(Report, null=True, on_delete=models.CASCADE)

    #Telephones

    #Web

    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class Crop(models.Model):
    # Main
    name = models.CharField(max_length=100, null=True)
    report = models.ForeignKey(Report, null=True, on_delete=models.CASCADE)
    dwu_formaula = models.CharField(max_length=100, null=True)
    season_start = models.DateField(null=True)
    critical_label1 = models.CharField(max_length=100, null=True)
    critical_label2 = models.CharField(max_length=100, null=True)
    critical_label3 = models.CharField(max_length=100, null=True)
    critical_label4 = models.CharField(max_length=100, null=True)
    critical_label5 = models.CharField(max_length=100, null=True)
    critical_label6 = models.CharField(max_length=100, null=True)
    critical_date1 = models.DateField(null=True)
    critical_date2 = models.DateField(null=True)
    critical_date3 = models.DateField(null=True)
    critical_date4 = models.DateField(null=True)
    critical_date5 = models.DateField(null=True)
    critical_date6 = models.DateField(null=True)
    season_end = models.DateField(null=True)

    # irrigations
    irrigation_method = models.IntegerField(choices=IRRIGATION_METHOD, default=1) # Drip
    irrigation_area = models.FloatField(default=0, null=True)
    irrigation_time = models.FloatField(default=0, null=True)
    irrigation_delivered_volume = models.FloatField(default=0, null=True)
    irrigation_position = models.FloatField(default=0, null=True, verbose_name="Monitoring position in")

    irrigation_upper = models.CharField(max_length=200, null=True)
    irrigation_lower = models.CharField(max_length=200, null=True)
    irrigation_crop_factor = models.IntegerField(default=0, null=True)
    irrigation_deliver_factor = models.IntegerField(default=0, null=True)
    irrigation_yield = models.IntegerField(default=0, null=True)

    irrigation_drip_days = models.IntegerField(default=0, null=True)
    irrigation_row_space = models.IntegerField(default=0, null=True)
    irrigation_emit_space = models.IntegerField(default=0, null=True)
    irrigation_plant_space = models.IntegerField(default=0, null=True)
    irrigation_wet_width = models.IntegerField(default=0, null=True)

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

class Site(models.Model):
    # Main
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    selected = models.BooleanField(null=True) #???
    name = models.CharField(max_length=100, null=True)
    variety = models.CharField(max_length=100, null=True)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, on_delete=models.CASCADE)
    season_start = models.DateField(null=True)
    bud_break = models.DateField(null=True)
    cd2 = models.DateField(null=True)
    cd3 = models.DateField(null=True)
    cd4 = models.DateField(null=True)
    cd5 = models.DateField(null=True)
    cd6 = models.DateField(null=True)
    season_end = models.DateField(null=True)

    # Irrigations
    irrigation_method = models.IntegerField(choices=IRRIGATION_METHOD, default=1) # Drip
    irrigation_area = models.FloatField(default=0, null=True)
    irrigation_time = models.FloatField(default=0, null=True)
    irrigation_delivered_volume = models.FloatField(default=0, null=True)
    irrigation_position = models.FloatField(default=0, null=True)
    irrigation_yield = models.FloatField(default=0, null=True)
    irrigation_allocation_volume = models.FloatField(default=0, null=True)
    # Equivalent depth and delivery rates are derived from above

    # Irrigarions and rain in

    # Root Zone
    rz1_top = models.IntegerField(default=0, null=True)
    rz1_bottom = models.IntegerField(default=0, null=True)
    rz2_top = models.IntegerField(default=0, null=True)
    rz2_bottom = models.IntegerField(default=0, null=True)
    rz3_top = models.IntegerField(default=0, null=True)
    rz3_bottom = models.IntegerField(default=0, null=True)

    # depth
    depth1 = models.IntegerField(default=0, null=True)
    depth2 = models.IntegerField(default=0, null=True)
    depth3 = models.IntegerField(default=0, null=True)
    depth4 = models.IntegerField(default=0, null=True)
    depth5 = models.IntegerField(default=0, null=True)
    depth6 = models.IntegerField(default=0, null=True)
    depth7 = models.IntegerField(default=0, null=True)
    depth8 = models.IntegerField(default=0, null=True)
    depth9 = models.IntegerField(default=0, null=True)
    depth10 = models.IntegerField(default=0, null=True)
    depth11 = models.IntegerField(default=0, null=True)
    depth12 = models.IntegerField(default=0, null=True)

    # Horison Equation
    depth_he1 = models.IntegerField(default=0, null=True)
    depth_he2 = models.IntegerField(default=0, null=True)
    depth_he3 = models.IntegerField(default=0, null=True)
    depth_he4 = models.IntegerField(default=0, null=True)
    depth_he5 = models.IntegerField(default=0, null=True)
    depth_he6 = models.IntegerField(default=0, null=True)
    depth_he7 = models.IntegerField(default=0, null=True)
    depth_he8 = models.IntegerField(default=0, null=True)
    depth_he9 = models.IntegerField(default=0, null=True)
    depth_he10 = models.IntegerField(default=0, null=True)
    depth_he11 = models.IntegerField(default=0, null=True)
    depth_he12 = models.IntegerField(default=0, null=True)

    created_date = models.DateTimeField('date published')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


#Site ID,Selected,Date,Type,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,SN,RZ1,RZ2,RZ3,DEFICIT,PDWU,EDWU,k1,k2,k3,k4,k5,k6,k7,k8,k9,k10,k11,k12,k13,k14,k15,k16,Comment3
class Reading(models.Model):
    # Preseume id is site
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    probe_date = models.DateTimeField()
