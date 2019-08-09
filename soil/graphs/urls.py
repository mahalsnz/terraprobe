from django.urls import path

from . import views
from .apiviews import VSWReadingList

app_name = 'graphs'

urlpatterns = [
    path("graphs/<int:site_id>/", views.first_graph),
    path("vsw_percentage/<int:site_id>/<int:year>/<int:month>/<int:day>/", views.vsw_percentage),
    path("example_graph", views.example_graph),
    path("api/vsw_reading/<int:pk>/", VSWReadingList.as_view(), name="vsw_data"),
    #This is through pandas rest
    #path("graphpandas/<int:pk>/",),
]
