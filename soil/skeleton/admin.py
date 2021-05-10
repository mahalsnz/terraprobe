from django.contrib import admin
from django.contrib.auth.models import User
from django import forms
from django.core import management
from django.contrib import messages
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Farm, Site, SiteDescription, Crop, Product, Reading
from .models import Report
from .models import Calibration
from .models import ReadingType
from .models import Probe
from .models import Season
from .models import ETReading
from .models import KCReading
from .models import Diviner
from .models import ProbeDiviner
from .models import CriticalDateType
from .models import CriticalDate, UserFullName
from .models import SeasonStartEnd
from .models import WeatherStation
from .models import Variety, VarietySeasonTemplate, Strategy, StrategyType

import logging
logger = logging.getLogger(__name__)

class StrategyAdmin(admin.ModelAdmin):
    list_display = ('type', 'critical_date_type', 'days', 'percentage')
    list_filter = ('type', 'critical_date_type')

class StrategyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage')

class WeatherStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code', 'average_rainfall')

class ProbeDivinerAdmin(admin.ModelAdmin):
    list_display = ('probe', 'diviner')

class DivinerAdmin(admin.ModelAdmin):
    list_display = ('diviner_number', 'site')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'site':
            kwargs["queryset"] = SiteDescription.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class KCReadingAdmin(admin.ModelAdmin):
    list_display = ('crop', 'period_from', 'period_to', 'kc')
    list_filter = ['crop']

class ETReadingAdmin(admin.ModelAdmin):
    list_display = ('date', 'state', 'daily')

class ReadingResource(resources.ModelResource):

    class Meta:
        model = Reading
        fields = ('site__name', 'site__site_number', 'site__farm__name', 'date', 'type', 'rain', 'meter', 'irrigation_litres', 'irrigation_mms', 'effective_rainfall', 'effective_irrigation','estimated_dwu')

class ReadingAdmin(ImportExportModelAdmin):
    list_display = ('site', 'type', 'date', 'serial_number', 'reviewed', 'depth1_count', 'comment')
    list_filter = ['type']
    search_fields = ['site__name', 'site__site_number']
    resource_class = ReadingResource

    def response_change(self, request, obj):
        if "_run-processes" in request.POST:
            try:
                sites = [obj.site]
                management.call_command('processrootzones', sites=sites)
                management.call_command('processmeter', sites=sites)
                management.call_command('processdailywateruse', sites=sites)
                management.call_command('processrainirrigation', sites=sites)
            except Exception as e:
                messages.error(request, "Error: " + str(e))
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

class ReadingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'comment', 'formula')

class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'formatted_season_start_year', 'current_flag')

class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'weatherstation')

class CalibrationAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'soil_type', 'period_from', 'period_to', 'slope', 'intercept')
    list_filter = ('serial_number', 'soil_type')
    search_fields = ['serial_number_id__serial_number']

class SiteAdmin(admin.ModelAdmin):
    list_display = ('site_number', 'name', 'farm', 'product', 'technician', 'is_active', 'latitude', 'longitude', 'application_rate')
    list_filter = ('is_active', 'technician')
    search_fields = ['site_number', 'name']
    fieldsets = [
        ('Main',        {'fields': ['site_number', 'farm', 'technician', 'name', 'product','comment', 'is_active','latitude', 'longitude', 'created_date', 'created_by']}),
        ('Irrigation',  {'fields': ['irrigation_method', 'irrigation_area', 'irrigation_time', 'irrigation_delivered_volume','irrigation_position','irrigation_yield','irrigation_allocation_volume'],
            'classes': ['collapse']}),
        ('Root Zones',
                    {'fields': ['rz1_bottom','rz2_bottom','rz3_bottom', 'rz_percentage'], 'classes': ['collapse']}),
        ('Depths',  {'fields': [('depth1', 'depth_he1'),('depth2', 'depth_he2'),('depth3', 'depth_he3'),('depth4', 'depth_he4'),
                                ('depth5', 'depth_he5'),('depth6', 'depth_he6'),('depth7', 'depth_he7'),('depth8', 'depth_he8'),
                                ('depth9', 'depth_he9'),('depth10', 'depth_he10')],'classes': ['collapse']}),
        ('Schedule',    {'fields': ['upper_limit', 'lower_limit', 'strategy', 'emitter_rate', 'row_spacing', 'emitter_spacing', 'plant_spacing'],
            'classes': ['collapse']}),
    ]
    radio_fields = {'irrigation_method': admin.HORIZONTAL}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'technician':
            kwargs["queryset"] = UserFullName.objects.filter(groups__name='Technician')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    #.values('first_name','last_name')

class ProductAdmin(admin.ModelAdmin):
    list_display = ['crop', 'variety']
    list_filter = ['crop']
    search_fields = ['variety', 'crop']

class ProbeAdmin(admin.ModelAdmin):
    list_display = ['id', 'serial_number', 'comment']

class CriticalDateTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'season_flag']

class CriticalDateAdmin(admin.ModelAdmin):
    list_display = ['site', 'season', 'type', 'date',]
    list_filter = ('season', 'type')
    search_fields = ['site__name', 'site__site_number']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'site':
            kwargs["queryset"] = SiteDescription.objects.all().order_by('site_number')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class SeasonStartEndAdmin(admin.ModelAdmin):
    list_display = ['site',  'season', 'period_from', 'period_to', 'season_current_flag', ]
    list_filter = ('season', 'season_current_flag')
    list_display_links = None

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class VarietySeasonTemplateAdmin(admin.ModelAdmin):
    list_display = ['variety', 'critical_date_type', 'formatted_variety_season_date']

admin.site.register(Site, SiteAdmin)
admin.site.register(Farm, FarmAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Crop)
admin.site.register(Reading, ReadingAdmin)
admin.site.register(Report)
admin.site.register(Calibration, CalibrationAdmin)
admin.site.register(ReadingType, ReadingTypeAdmin)
admin.site.register(Probe, ProbeAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(ETReading, ETReadingAdmin)
admin.site.register(KCReading, KCReadingAdmin)
admin.site.register(Diviner, DivinerAdmin)
admin.site.register(ProbeDiviner, ProbeDivinerAdmin)
admin.site.register(CriticalDateType, CriticalDateTypeAdmin)
admin.site.register(CriticalDate, CriticalDateAdmin)
admin.site.register(SeasonStartEnd, SeasonStartEndAdmin)
admin.site.register(WeatherStation, WeatherStationAdmin)
admin.site.register(Variety)
admin.site.register(VarietySeasonTemplate, VarietySeasonTemplateAdmin)
admin.site.register(Strategy, StrategyAdmin)
admin.site.register(StrategyType, StrategyTypeAdmin)
