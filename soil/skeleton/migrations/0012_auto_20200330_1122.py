# Generated by Django 2.2.1 on 2020-03-29 22:22

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('skeleton', '0011_auto_20200320_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategy',
            name='percentage',
            field=models.FloatField(help_text='A percentage number between 0 and 100 indicating the variation from the limit associated with the strategy.'),
        ),
        migrations.AlterUniqueTogether(
            name='crop',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='crop',
            name='variety',
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date published')),
                ('created_by', models.ForeignKey(default=django.contrib.auth.models.User, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('crop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Crop')),
                ('report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Report')),
                ('variety', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='skeleton.Variety')),
            ],
            options={
                'unique_together': {('crop', 'variety')},
            },
        ),
    ]
