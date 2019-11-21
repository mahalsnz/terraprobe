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

import datetime
from django.urls import register_converter

class IsoDateConverter:
    regex = '\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()

    def to_url(self, value):
        return str(value)

register_converter(IsoDateConverter, 'isodate')

urlpatterns = [
    path('', include('skeleton.urls')),
    path('admin/', admin.site.urls, name='admin'),
    path('graphs/', include('graphs.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

admin.site.site_header = "Fruition Soil Moisture Administration"
admin.site.site_title = "Fruition Soil Moisture Administration Portal"
admin.site.index_title = "Welcome to the Fruition Soil Moisture Administration Portal"
