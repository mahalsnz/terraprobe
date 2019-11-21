from django.urls import path

from . import views
from .apiviews import VSWReadingList

app_name = 'graphs'

urlpatterns = [
    path("graphs/<int:site_id>/", views.first_graph),
    path("api/vsw_reading/<int:pk>/", VSWReadingList.as_view(), name="vsw_data"),
    #path("api/vsw_reading/<int:pk>/<isodate:date>/<isodate:date>/", VSWReadingList.as_view(), name="vsw_data"),
    #This is through pandas rest
    #path("graphpandas/<int:pk>/",),
]
