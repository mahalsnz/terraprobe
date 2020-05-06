# tables.py
import django_tables2 as tables
from django_tables2 import SingleTableView
from .models import Site

class SiteReportTable(tables.Table):

    '''
    def get_top_pinned_data(self):
        return [
            {"name": "Block D"}
        ]
    '''

    class Meta:
        model = Site
        fields = ("site_number", "name", "farm", "product")
        orderable = True
