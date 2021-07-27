"""soil URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt import views as jwt_views

import datetime
from django.urls import register_converter

API_TITLE = 'Terraprobe'
API_DESCRIPTION = 'A Web API for retrieving Terraprobe data.'
schema_view = get_schema_view(title=API_TITLE)

class IsoDateConverter:
    regex = '\d{2}-\d{2}-\d{4}'

    def to_python(self, value):
        return datetime.datetime.strptime(value, '%d-%m-%Y').date()

    def to_url(self, value):
        return str(value)

register_converter(IsoDateConverter, 'isodate')

urlpatterns = [
    path('', include('skeleton.urls')),
    path('admin/', admin.site.urls, name='admin'),
    path('api-auth/', include('rest_framework.urls')),
    path('graphs/', include('graphs.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    path('schema/', schema_view),
]

admin.site.site_header = "Fruition Soil Moisture Administration"
admin.site.site_title = "Fruition Soil Moisture Administration Portal"
admin.site.index_title = "Welcome to the Fruition Soil Moisture Administration Portal"

# curl --insecure -X POST -H "Content-Type: application/json" -d '{"username": "mabbettb", "password": ""}' https://staging.terraprobe.mahal.co.nz/api/token/
# curl --insecure -X GET -H "Content-Type: application/json" -d '{"Authorization: Bearer token"}' https://staging.terraprobe.mahal.co.nz/api/site/
