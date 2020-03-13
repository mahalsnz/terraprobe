from django.db import models

class Farm(models.Model):
    name = models.CharField(max_length=100, null=False)

    class Meta:
        managed = False
        db_table = "graphs_farm"

class Site(models.Model):
    name = models.CharField(max_length=100, null=False)

    class Meta:
        managed = False
        db_table = "graphs_site"

class ReadingType(models.Model):
    name = models.CharField(max_length=100, null=False)

    class Meta:
        managed = False
        db_table = "graphs_readingtype"

class vsw_reading(models.Model):
    date = models.DateField(null=False)
    site = models.ForeignKey(Site, primary_key=True, on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    reading_type = models.ForeignKey(ReadingType, on_delete=models.CASCADE)
    type = models.TextField()
    crop_id = models.IntegerField()
    rz1_top = models.IntegerField()
    rz1_bottom = models.IntegerField()
    rz1 = models.FloatField()
    rz2 = models.FloatField()
    rz3 = models.FloatField()
    probe_dwu = models.FloatField()
    estimated_dwu = models.FloatField()
    deficit = models.FloatField()
    meter = models.FloatField()
    irrigation_litres = models.FloatField()
    irrigation_mms = models.FloatField()
    rain = models.FloatField()
    effective_rain_1 = models.FloatField()
    effective_rainfall = models.FloatField()
    effective_irrigation = models.FloatField()
    comment = models.TextField()
    depth1 = models.IntegerField()
    count1 = models.FloatField()
    vsw1 = models.FloatField()
    vsw1_perc = models.FloatField()
    depth2 = models.IntegerField()
    count2 = models.FloatField()
    vsw2 = models.FloatField()
    vsw2_perc = models.FloatField()
    depth3 = models.IntegerField()
    count3 = models.FloatField()
    vsw3 = models.FloatField()
    vsw3_perc = models.FloatField()
    depth4 = models.IntegerField()
    count4 = models.FloatField()
    vsw4 = models.FloatField()
    vsw4_perc = models.FloatField()
    depth5 = models.IntegerField()
    count5 = models.FloatField()
    vsw5 = models.FloatField()
    vsw5_perc = models.FloatField()
    depth6 = models.IntegerField()
    count6 = models.FloatField()
    vsw6 = models.FloatField()
    vsw6_perc = models.FloatField()
    depth7 = models.IntegerField()
    count7 = models.FloatField()
    vsw7 = models.FloatField()
    vsw7_perc = models.FloatField()
    depth8 = models.IntegerField()
    count8 = models.FloatField()
    vsw8 = models.FloatField()
    vsw8_perc = models.FloatField()
    depth9 = models.IntegerField()
    count9 = models.FloatField()
    vsw9 = models.FloatField()
    vsw9_perc = models.FloatField()
    depth10 = models.IntegerField()
    count10 = models.FloatField()
    vsw10 = models.FloatField()
    vsw10_perc = models.FloatField()

    class Meta:
        managed = False
        db_table = "graphs_vsw"
