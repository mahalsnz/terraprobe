from django.urls import path

from . import views
#from .view import GraphView
#from skeleton.apiviews import SiteReadingList

app_name = 'graphs'

urlpatterns = [
    path("graphs/<int:site_id>/", views.first_graph),
    path("example_graph", views.example_graph),
    #This is through pandas rest
    #path("graphpandas/<int:pk>/",),
]
