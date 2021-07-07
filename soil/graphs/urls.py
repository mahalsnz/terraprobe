from django.urls import path
from django.views.decorators.cache import cache_page

from . import views
from .apiviews import VSWReadingList, VSWReadingReadyList, VSWStrategyList, VSWDateList, VSWDateListV2, FruitionSummary, FruitionSummaryV2, EOYFarmSummary

app_name = 'graphs'

urlpatterns = [
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWReadingList.as_view(), name="vsw_data"),
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/<str:reviewed>/", cache_page(60 * 30)(VSWReadingReadyList.as_view()), name="vsw_data"),
    path("api/vsw_strategy/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWStrategyList.as_view(), name="vsw_strategy"),
    path("api/vsw_date/<int:pk>/", cache_page(60 * 30)(VSWDateList.as_view())),
    path("api/v2/vsw_date/<int:season_id>/<int:site_id>/", cache_page(60 * 30)(VSWDateListV2.as_view())),
    path("customer_weekly/<int:site_id>/", views.customer_weekly, name="customer_weekly"),

    path("api/v1/fruition_summary/<str:site_ids>/", cache_page(60 * 30)(FruitionSummary.as_view())),
    path("api/v2/fruition_summary/<str:site_ids>/", cache_page(60 * 30)(FruitionSummaryV2.as_view())),
    path("api/v1/eoy_farm_report/<int:farm_id>/<int:season_id>/<int:template_id>/", cache_page(60*60*4)(EOYFarmSummary.as_view())), # Cache for 4 hours. Very unlikely to have changes
]
