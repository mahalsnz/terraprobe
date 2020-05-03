# tables.py
import django_tables2 as tables
from django_tables2 import SingleTableView
from .models import Site

class SiteDatesTable(tables.Table):
    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "product")
        orderable = True

class SiteMissingReadingTypesTable(tables.Table):
    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "product")
        orderable = True
