from django.contrib import admin

from .models import Farm
from .models import Site
from .models import Crop
from .models import Reading
from .models import Report
from .models import Calibration

# wOULD BE NICE
#class DepthInline(admin.TabularInline):
#    model = Site
#    fields = ('depth1', 'depth_he1')

class SiteAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Main',        {'fields': ['farm','name','variety','crop','season_start', 'bud_break', 'cd2', 'cd3', 'cd4', 'cd5', 'cd6', 'season_end','created_date', 'created_by']}),
        ('Irrigation',  {'fields': ['irrigation_method', 'irrigation_area', 'irrigation_time', 'irrigation_delivered_volume','irrigation_position','irrigation_yield','irrigation_allocation_volume'],
            'classes': ['collapse']}),
        ('Root Zones',  {'fields': ['rz1_top','rz1_bottom','rz2_top','rz2_bottom','rz3_top','rz3_bottom'], 'classes': ['collapse']}),
        ('Depths',  {'fields': [('depth1', 'depth_he1'),('depth2', 'depth_he2'),('depth3', 'depth_he3'),('depth4', 'depth_he4'),
                                ('depth5', 'depth_he5'),('depth6', 'depth_he6'),('depth7', 'depth_he7'),('depth8', 'depth_he8'),
                                ('depth9', 'depth_he9'),('depth10', 'depth_he10'),('depth11', 'depth_he11'),('depth12', 'depth_he12')],'classes': ['collapse']}),
    ]
    radio_fields = {'irrigation_method': admin.HORIZONTAL}
class CropAdmin(admin.ModelAdmin):
    list_display = ['name']
    fieldsets = [
        ('Main',        {'fields': ['name', 'report','dwu_formaula', 'created_date', 'created_by']}),
        ('Dates',       {'fields': ['season_start',('critical_label1','critical_date1'), ('critical_label2','critical_date2'), ('critical_label3','critical_date3'),
                                    ('critical_label4','critical_date4'), ('critical_label5','critical_date5'), ('critical_label6','critical_date6'),'season_end'],'classes': ['collapse']}),
        ('Irrigations', {'fields': ['irrigation_method', 'irrigation_area', 'irrigation_time', 'irrigation_delivered_volume','irrigation_position',
                                    'irrigation_upper', 'irrigation_lower', 'irrigation_crop_factor', 'irrigation_deliver_factor', 'irrigation_yield',
                                    'irrigation_drip_days', 'irrigation_row_space', 'irrigation_emit_space', 'irrigation_plant_space', 'irrigation_wet_width'],'classes': ['collapse']}),
    ]
    radio_fields = {'irrigation_method': admin.HORIZONTAL}

admin.site.register(Site, SiteAdmin)
admin.site.register(Farm)
admin.site.register(Crop, CropAdmin)
admin.site.register(Reading)
admin.site.register(Report)
admin.site.register(Calibration)
