from django import forms
from .models import Document, Reading, Season, Site, UserFullName, SiteDescription

from django.forms import ModelChoiceField

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']

class SiteReadingsForm(forms.ModelForm):
    site = forms.ModelChoiceField(queryset=SiteDescription.objects.all(), widget=forms.Select())
    technician = forms.ModelChoiceField(queryset=UserFullName.objects.filter(groups__name='Technician'), widget=forms.Select())
    season = forms.ModelChoiceField(Season.objects.all().order_by('-current_flag'), empty_label=None, widget=forms.Select()) # current season is at top

    class Meta:
        model = Reading
        fields = ()

    # Override
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['season'].queryset = Season.objects.none()
        #self.fields['country'].queryset = Country.objects.none()
