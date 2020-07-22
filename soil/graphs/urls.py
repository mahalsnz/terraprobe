from django.urls import path

from . import views
from .apiviews import VSWReadingList, VSWStrategyList, VSWDateList

app_name = 'graphs'

urlpatterns = [
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWReadingList.as_view(), name="vsw_data"),
    path("api/vsw_strategy/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWStrategyList.as_view(), name="vsw_strategy"),
    path("api/vsw_date/<int:pk>/", VSWDateList.as_view(), name="vsw_date"),
    path("customer_weekly/<int:site_id>/", views.customer_weekly, name="customer_weekly"),
]
