from django import forms
from .models import Document, Reading, ReadingType, Season, Site, UserFullName, SiteDescription, Crop, CriticalDate, SeasonStartEnd
from address.models import State
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from django.forms import ModelChoiceField, ModelMultipleChoiceField
from bootstrap_datepicker_plus import DatePickerInput

class SeasonConfirmationForm(forms.Form):
    confirm = forms.BooleanField(required=False)

class SelectCropRegionSeasonForm(forms.Form):
    crop = forms.ModelMultipleChoiceField(queryset = Crop.objects.all().order_by('name'))
    region = forms.ModelMultipleChoiceField(queryset = State.objects.all().order_by('name'))
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), widget=forms.Select(), required=True, empty_label=None)

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
    select_copy = forms.BooleanField(required=False)

class CreateRefillFullPointForm(forms.Form):
    fullpoint_value = forms.FloatField(required=False,)
    refill_value = forms.FloatField(required=False)
    copy = forms.BooleanField(required=False)

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Document
        fields = ['description', 'document']

class SiteReadingsForm(forms.ModelForm):
    #site = forms.ModelChoiceField(queryset=SiteDescription.objects.all(), widget=forms.Select().order_by('-site_number'))
    site = forms.ModelChoiceField(SiteDescription.objects.all().order_by('-site_number'), widget=forms.Select())
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
