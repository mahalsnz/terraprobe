# Generated by Django 3.0.6 on 2020-08-18 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skeleton', '0020_auto_20200615_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='reading',
            name='reviewed',
            field=models.BooleanField(default=False, help_text='Has reading been reviewed. Only really applies to Probe readings.', null=True),
        ),
    ]
