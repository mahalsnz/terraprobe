from django.urls import path
from django.views.decorators.cache import cache_page

from . import views
from .apiviews import VSWReadingList, VSWReadingReadyList, VSWStrategyList, VSWDateList, FruitionSummary, FruitionSummaryV2

app_name = 'graphs'

urlpatterns = [
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWReadingList.as_view(), name="vsw_data"),
    path("api/vsw_reading/<int:pk>/<isodate:period_from>/<isodate:period_to>/<str:reviewed>/", VSWReadingReadyList.as_view(), name="vsw_data"),
    path("api/vsw_strategy/<int:pk>/<isodate:period_from>/<isodate:period_to>/", VSWStrategyList.as_view(), name="vsw_strategy"),
    path("api/vsw_date/<int:pk>/", VSWDateList.as_view(), name="vsw_date"),
    path("customer_weekly/<int:site_id>/", views.customer_weekly, name="customer_weekly"),
    #path("api/v1/fruition_summary/<int:pk>/", FruitionSummary.as_view()),
    path("api/v1/fruition_summary/<str:site_ids>/", FruitionSummary.as_view()),
    path("api/v2/fruition_summary/<str:site_ids>/", cache_page(60 * 15)(FruitionSummaryV2.as_view())),
]
