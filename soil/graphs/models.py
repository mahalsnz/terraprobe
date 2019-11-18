from django.db import models

class Farm(models.Model):
    name = models.CharField(max_length=100, null=False)

    class Meta:
        managed = False
        db_table = "graphs_farm"

class Site(models.Model):
    name = models.CharField(max_length=100, null=False)
    variety = models.CharField(max_length=100, null=False)

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
    #crop_id = models.IntegerField()
    meter = models.FloatField()
    rain = models.FloatField()
    depth1 = models.IntegerField()
    count1 = models.FloatField()
    vsw1 = models.FloatField()
    depth2 = models.IntegerField()
    count2 = models.FloatField()
    vsw2 = models.FloatField()
    depth3 = models.IntegerField()
    count3 = models.FloatField()
    vsw3 = models.FloatField()
    depth4 = models.IntegerField()
    count4 = models.FloatField()
    vsw4 = models.FloatField()
    depth5 = models.IntegerField()
    count5 = models.FloatField()
    vsw5 = models.FloatField()
    depth6 = models.IntegerField()
    count6 = models.FloatField()
    vsw6 = models.FloatField()
    depth7 = models.IntegerField()
    count7 = models.FloatField()
    vsw7 = models.FloatField()
    depth8 = models.IntegerField()
    count8 = models.FloatField()
    vsw8 = models.FloatField()
    depth9 = models.IntegerField()
    count9 = models.FloatField()
    vsw9 = models.FloatField()

    class Meta:
        managed = False
        db_table = "graphs_vsw"
