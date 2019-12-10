from django import forms
from .models import Document, Reading, Season, Site, UserFullName, SiteDescription, Crop, CriticalDate, SeasonStartEnd
from address.models import State
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from django.forms import ModelChoiceField
from .widgets import BootstrapDateTimePickerInput

class SeasonStartEndForm(forms.ModelForm):
    crop = forms.ModelChoiceField(Crop.objects.all().order_by('name'), widget=forms.Select())
    region = forms.ModelChoiceField(State.objects.all().order_by('name'), widget=forms.Select())
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), widget=forms.Select())

    period_from = forms.DateTimeField(
        input_formats=['%d/%m/%Y'],
        widget=BootstrapDateTimePickerInput()
    )

    period_to = forms.DateTimeField(
        input_formats=['%d/%m/%Y'],
        widget=BootstrapDateTimePickerInput()
    )

    class Meta:
        model = CriticalDate
        fields = ()

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    '''
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    '''
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
