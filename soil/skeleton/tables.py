# tables.py
import django_tables2 as tables
from .models import Site

class SiteDatesTable(tables.Table):
    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "crop")

class SiteMissingReadingTypesTable(tables.Table):
    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "crop")
