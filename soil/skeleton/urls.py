from django.urls import path

from . import views
from .apiviews import FarmList, FarmDetail, ReadingDetail, ReadingList

app_name = 'skeleton'

urlpatterns = [
    path('', views.index, name='index'),
    path("api/farm/", FarmList.as_view(), name="farms_list"),
    path("api/farm/<int:pk>/", FarmDetail.as_view(), name="farms_detail"),
    #path("api/reading/", ReadingList.as_view(), name="readings_list"),
    path("api/reading/<int:pk>/", ReadingDetail.as_view(), name="readings_detail")
]
