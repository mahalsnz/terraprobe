from django.urls import path
from django.conf.urls import url

from .views import SiteReadingsView, UploadReadingsFileView, SeasonWizard
from . import views
from .forms import SelectCropRegionSeasonForm, CreateSeasonStartEndForm, CreateRefillFullPointForm, SeasonConfirmationForm

from .apiviews import ReportList, ReportDetail, SeasonList, SeasonDetail, ReadingTypeList, ReadingTypeDetail \
, FarmList, FarmDetail, ReadingDetail, ReadingList, SiteReadingList, SiteList, SiteDetail

FORMS = [("select_crsf", SelectCropRegionSeasonForm),
         ("create_ssef", CreateSeasonStartEndForm),
         ("create_rfpr", CreateRefillFullPointForm),
         ("season_confirmation", SeasonConfirmationForm),]

urlpatterns = [
    path('', views.index, name='home'),
    path('reports', views.report_home, name='report_home'),
    path('readings/site/', SiteReadingsView.as_view(), name='site_readings'),
    path('upload_readings_file/', UploadReadingsFileView.as_view(), name='upload_readings_file'),
    path('season_wizard/', SeasonWizard.as_view(FORMS), name='season_wizard'),

    #path("vsw_percentage/<int:site_id>/<int:year>/<int:month>/<int:day>/", views.vsw_percentage),
    path("vsw_percentage/<int:site_id>/<isodate:date>/", views.vsw_percentage),
    # API
    path("api/report/", ReportList.as_view(), name="reports_list"),
    path("api/report/<int:pk>/", ReportDetail.as_view(), name="reports_detail"),
    path("api/season/", SeasonList.as_view(), name="seasons_list"),
    path("api/season/<int:pk>/", SeasonDetail.as_view(), name="seasons_detail"),
    path("api/reading_type/", ReadingTypeList.as_view(), name="reading_types_list"),
    path("api/reading_type/<int:pk>/", ReadingTypeDetail.as_view(), name="reading_types_detail"),
    path("api/farm/", FarmList.as_view(), name="farms_list"),
    path("api/farm/<int:pk>/", FarmDetail.as_view(), name="farms_detail"),
    path("api/site/", SiteList.as_view(), name="sites_list"),
    path("api/site/<int:pk>/", SiteDetail.as_view(), name="sites_detail"),
    path("api/reading/", ReadingList.as_view(), name="readings_list"),
    path("api/reading/<int:pk>/", ReadingDetail.as_view(), name="readings_detail"),
    path("api/site_reading/<int:pk>/", SiteReadingList.as_view(), name="graph_data"),

    #ajax
    path('ajax/load-sites/', views.load_sites, name='ajax_load_sites'),
    path('ajax/load-site-readings/', views.load_site_readings, name='ajax_load_site_readings'),
    path('ajax/load-graph/', views.load_graph, name='ajax_load_graph'),
]
