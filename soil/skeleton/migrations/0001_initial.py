# Generated by Django 2.2.1 on 2019-06-24 22:46

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address', '0002_auto_20160213_1726'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('dwu_formaula', models.CharField(blank=True, max_length=100, null=True)),
                ('season_start', models.DateField(blank=True, null=True)),
                ('critical_label1', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_label2', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_label3', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_label4', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_label5', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_label6', models.CharField(blank=True, max_length=100, null=True)),
                ('critical_date1', models.DateField(blank=True, null=True)),
                ('critical_date2', models.DateField(blank=True, null=True)),
                ('critical_date3', models.DateField(blank=True, null=True)),
                ('critical_date4', models.DateField(blank=True, null=True)),
                ('critical_date5', models.DateField(blank=True, null=True)),
                ('critical_date6', models.DateField(blank=True, null=True)),
                ('season_end', models.DateField(blank=True, null=True)),
                ('irrigation_method', models.IntegerField(choices=[(0, 'Non-Drip (Overhead)'), (1, 'Drip')], default=1)),
                ('irrigation_area', models.FloatField(blank=True, null=True)),
                ('irrigation_time', models.FloatField(blank=True, null=True)),
                ('irrigation_delivered_volume', models.FloatField(blank=True, null=True)),
                ('irrigation_position', models.FloatField(blank=True, null=True, verbose_name='Monitoring position in')),
                ('irrigation_upper', models.CharField(blank=True, max_length=200, null=True)),
                ('irrigation_lower', models.CharField(blank=True, max_length=200, null=True)),
                ('irrigation_crop_factor', models.IntegerField(blank=True, null=True)),
                ('irrigation_deliver_factor', models.IntegerField(blank=True, null=True)),
                ('irrigation_yield', models.IntegerField(blank=True, null=True)),
                ('irrigation_drip_days', models.IntegerField(blank=True, null=True)),
                ('irrigation_row_space', models.IntegerField(blank=True, null=True)),
                ('irrigation_emit_space', models.IntegerField(blank=True, null=True)),
                ('irrigation_plant_space', models.IntegerField(blank=True, null=True)),
                ('irrigation_wet_width', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Farm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('owner', models.CharField(blank=True, max_length=100, null=True)),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('landline', models.CharField(max_length=40, null=True)),
                ('mobile', models.CharField(max_length=40, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('folder', models.CharField(max_length=100, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='address.Address')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected', models.BooleanField(null=True)),
                ('name', models.CharField(max_length=100, null=True)),
                ('variety', models.CharField(max_length=100, null=True)),
                ('season_start', models.DateField(blank=True, null=True)),
                ('bud_break', models.DateField(blank=True, null=True)),
                ('cd2', models.DateField(blank=True, null=True)),
                ('cd3', models.DateField(blank=True, null=True)),
                ('cd4', models.DateField(blank=True, null=True)),
                ('cd5', models.DateField(blank=True, null=True)),
                ('cd6', models.DateField(blank=True, null=True)),
                ('season_end', models.DateField(blank=True, null=True)),
                ('irrigation_method', models.IntegerField(choices=[(0, 'Non-Drip (Overhead)'), (1, 'Drip')], default=1)),
                ('irrigation_area', models.FloatField(blank=True, null=True)),
                ('irrigation_time', models.FloatField(blank=True, null=True)),
                ('irrigation_delivered_volume', models.FloatField(blank=True, null=True)),
                ('irrigation_position', models.FloatField(blank=True, null=True)),
                ('irrigation_yield', models.FloatField(blank=True, null=True)),
                ('irrigation_allocation_volume', models.FloatField(blank=True, null=True)),
                ('rz1_top', models.IntegerField(blank=True, null=True)),
                ('rz1_bottom', models.IntegerField(blank=True, null=True)),
                ('rz2_top', models.IntegerField(blank=True, null=True)),
                ('rz2_bottom', models.IntegerField(blank=True, null=True)),
                ('rz3_top', models.IntegerField(blank=True, null=True)),
                ('rz3_bottom', models.IntegerField(blank=True, null=True)),
                ('depth1', models.IntegerField(blank=True, null=True)),
                ('depth2', models.IntegerField(blank=True, null=True)),
                ('depth3', models.IntegerField(blank=True, null=True)),
                ('depth4', models.IntegerField(blank=True, null=True)),
                ('depth5', models.IntegerField(blank=True, null=True)),
                ('depth6', models.IntegerField(blank=True, null=True)),
                ('depth7', models.IntegerField(blank=True, null=True)),
                ('depth8', models.IntegerField(blank=True, null=True)),
                ('depth9', models.IntegerField(blank=True, null=True)),
                ('depth10', models.IntegerField(blank=True, null=True)),
                ('depth11', models.IntegerField(blank=True, null=True)),
                ('depth12', models.IntegerField(blank=True, null=True)),
                ('depth_he1', models.IntegerField(blank=True, null=True)),
                ('depth_he2', models.IntegerField(blank=True, null=True)),
                ('depth_he3', models.IntegerField(blank=True, null=True)),
                ('depth_he4', models.IntegerField(blank=True, null=True)),
                ('depth_he5', models.IntegerField(blank=True, null=True)),
                ('depth_he6', models.IntegerField(blank=True, null=True)),
                ('depth_he7', models.IntegerField(blank=True, null=True)),
                ('depth_he8', models.IntegerField(blank=True, null=True)),
                ('depth_he9', models.IntegerField(blank=True, null=True)),
                ('depth_he10', models.IntegerField(blank=True, null=True)),
                ('depth_he11', models.IntegerField(blank=True, null=True)),
                ('depth_he12', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('crop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Crop')),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='skeleton.Farm')),
                ('report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Report')),
            ],
        ),
        migrations.CreateModel(
            name='Reading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('depth1', models.FloatField(blank=True, null=True)),
                ('depth2', models.FloatField(blank=True, null=True)),
                ('depth3', models.FloatField(blank=True, null=True)),
                ('depth4', models.FloatField(blank=True, null=True)),
                ('depth5', models.FloatField(blank=True, null=True)),
                ('depth6', models.FloatField(blank=True, null=True)),
                ('depth7', models.FloatField(blank=True, null=True)),
                ('depth8', models.FloatField(blank=True, null=True)),
                ('depth9', models.FloatField(blank=True, null=True)),
                ('depth10', models.FloatField(blank=True, null=True)),
                ('depth11', models.FloatField(blank=True, null=True)),
                ('depth12', models.FloatField(blank=True, null=True)),
                ('probe_dwu', models.FloatField(blank=True, null=True)),
                ('estimated_dwu', models.FloatField(blank=True, null=True)),
                ('rain', models.FloatField(blank=True, null=True)),
                ('meter', models.FloatField(blank=True, null=True)),
                ('irrigation_litres', models.FloatField(blank=True, null=True)),
                ('irrigation_mms', models.FloatField(blank=True, null=True)),
                ('effective_rain_1', models.FloatField(blank=True, null=True)),
                ('effective_rainfall', models.FloatField(blank=True, null=True)),
                ('efflrr1', models.FloatField(blank=True, null=True)),
                ('efflrr2', models.FloatField(blank=True, null=True)),
                ('effective_irrigation', models.FloatField(blank=True, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='skeleton.Site')),
            ],
        ),
        migrations.AddField(
            model_name='farm',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Report'),
        ),
        migrations.AddField(
            model_name='crop',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Report'),
        ),
        migrations.CreateModel(
            name='Calibration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.IntegerField(default=0, null=True)),
                ('soil_type', models.IntegerField(blank=True, null=True)),
                ('slope', models.FloatField(blank=True, null=True)),
                ('intercept', models.FloatField(blank=True, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='skeleton.Site')),
            ],
        ),
    ]