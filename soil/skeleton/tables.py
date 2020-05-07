# tables.py
import django_tables2 as tables
from django_tables2 import SingleTableView
from .models import Site

class SiteReportTable(tables.Table):
    site_number = tables.Column()
    name = tables.Column()
    farm = tables.Column()
    product = tables.Column()

    '''
    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "product")
        orderable = True
    '''
