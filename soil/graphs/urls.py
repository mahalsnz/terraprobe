from django.urls import path

from . import views
from .apiviews import VSWReadingList, VSWStrategyList

app_name = 'graphs'

urlpatterns = [
    path("graphs/<int:site_id>/", views.first_graph),
    #path("api/vsw_reading/<int:pk>/", VSWReadingList.as_view(), name="vsw_data"),
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWReadingList.as_view(), name="vsw_data"),
    path("api/vsw_strategy/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWStrategyList.as_view(), name="vsw_strategy"),
]
