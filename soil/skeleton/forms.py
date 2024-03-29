from django import forms
from .models import (Probe, SoilProfileType, ProbeDiviner, Diviner, Document, Reading, ReadingType, Season, Farm, Site, UserFullName, SiteDescription,
    Product, CriticalDate, SeasonStartEnd)
from address.models import State
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from django.forms.widgets import TextInput

from django.forms import ModelChoiceField, ModelMultipleChoiceField, ModelForm, CheckboxInput
from bootstrap_datepicker_plus import DatePickerInput
import datetime
from dal import autocomplete

class SoilProfileTypeForm(ModelForm):
    class Meta:
        model = SoilProfileType
        fields = '__all__'
        widgets = {
            'color': TextInput(attrs={'type': 'color'}),
        }

class CreateSeasonResourcesForm(forms.ModelForm):
    season_from = forms.ModelChoiceField(Season.objects.all().order_by('-season_date'), empty_label=None, widget=forms.Select())
    season_to = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), empty_label=None, widget=forms.Select())
    critical_date = forms.BooleanField(initial=True)
    crop_coefficient = forms.BooleanField(initial=True)
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.layout = Layout('farm','season')

    class Meta:
        model = Season
        fields = []


class EOYReportForm(forms.ModelForm):
    farm = forms.ModelChoiceField(Farm.objects.all().order_by('name'), widget=forms.Select())
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), empty_label=None, widget=forms.Select())
    template = forms.ModelChoiceField(Document.objects.filter(description='EOY'), empty_label=None, widget=forms.Select())
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.layout = Layout('farm','season')

    class Meta:
        model = Farm
        fields = ['id',]

class DivinerForm(forms.ModelForm):
    probe = forms.ModelChoiceField(Probe.objects.all(), widget=forms.Select())
    site = forms.ModelChoiceField(SiteDescription.objects.filter(is_active=True).order_by('site_number'), widget=forms.Select())

    class Meta:
        model = Diviner
        fields = ['diviner_number', 'site']

class SiteReportReadyForm(forms.ModelForm):
    date = forms.DateField(
        widget = DatePickerInput(format='%Y-%m-%d'),
        required = False,
        initial=datetime.date.today,
    )

    class Meta:
        model = Reading
        fields = ['id',]

class SiteSelectionForm(forms.ModelForm):
    site_number = forms.ModelChoiceField(
        queryset=SiteDescription.objects.filter(is_active=True),
        widget=autocomplete.ModelSelect2(url='autocomplete_sitenumber')
    )
    date = forms.DateField(
        widget = DatePickerInput(format='%Y-%m-%d'),
        required = False,
        initial=datetime.date.today,
    )
    meter = forms.IntegerField(required=False)
    rain = forms.IntegerField(required=False)

    class Meta:
        model = Site
        fields = ['id',]

class SelectCropRegionSeasonForm(forms.Form):
    product = forms.ModelMultipleChoiceField(queryset = Product.objects.all().order_by('crop'))
    region = forms.ModelMultipleChoiceField(queryset = State.objects.all().order_by('name'))
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), widget=forms.Select(), required=True, empty_label=None)
    multi_year_season = forms.BooleanField(required=False, initial=True)
    refill_fullpoint_copy = forms.BooleanField(required=False, initial=True)

class CreateSeasonStartEndForm(forms.Form):
    period_from = forms.DateField(
        widget = DatePickerInput(
        ),
        required = False,
    )

    period_to = forms.DateField(
        widget=DatePickerInput(),
        required=False
    )
    seasons_copy = forms.BooleanField(required=False)

class CreateRefillFullPointForm(forms.Form):
    fullpoint_depth1_value = forms.FloatField(required=False)
    refill_depth1_value = forms.FloatField(required=False)
    fullpoint_depth2_value = forms.FloatField(required=False)
    refill_depth2_value = forms.FloatField(required=False)
    fullpoint_depth3_value = forms.FloatField(required=False)
    refill_depth3_value = forms.FloatField(required=False)
    fullpoint_depth4_value = forms.FloatField(required=False)
    refill_depth4_value = forms.FloatField(required=False)
    fullpoint_depth5_value = forms.FloatField(required=False)
    refill_depth5_value = forms.FloatField(required=False)
    fullpoint_depth6_value = forms.FloatField(required=False)
    refill_depth6_value = forms.FloatField(required=False)
    fullpoint_depth7_value = forms.FloatField(required=False)
    refill_depth7_value = forms.FloatField(required=False)
    fullpoint_depth8_value = forms.FloatField(required=False)
    refill_depth8_value = forms.FloatField(required=False)
    fullpoint_depth9_value = forms.FloatField(required=False)
    refill_depth9_value = forms.FloatField(required=False)
    fullpoint_depth10_value = forms.FloatField(required=False)
    refill_depth10_value = forms.FloatField(required=False)
    types_copy = forms.BooleanField(required=False)

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Document
        fields = ['description', 'document']

class SiteReadingsForm(forms.ModelForm):

    farm = forms.ModelChoiceField(Farm.objects.all().order_by('-name'), widget=forms.Select())
    site = forms.ModelChoiceField(SiteDescription.objects.filter(is_active=True).order_by('site_number'), widget=forms.Select())
    technician = forms.ModelChoiceField(queryset=UserFullName.objects.filter(groups__name='Technician'), widget=forms.Select())
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), empty_label=None, widget=forms.Select()) # current season is at top
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.layout = Layout('site','technician','season')

    class Meta:
        model = Reading
        fields = ()

    # Override
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['season'].queryset = Season.objects.none()
        #self.fields['country'].queryset = Country.objects.none()
