from django.contrib import admin

from .models import Farm
from .models import Site
from .models import Crop
from .models import Reading

class SiteAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Main',        {'fields': ['farm','name','variety','crop','season_start','season_end']}),
        ('Irrigation',  {'fields': ['irrigation_drip', 'irrigation_area', 'irrigation_time'], 'classes': ['collapse']}),
    ]

admin.site.register(Site, SiteAdmin)
admin.site.register(Farm)
admin.site.register(Crop)
admin.site.register(Reading)
