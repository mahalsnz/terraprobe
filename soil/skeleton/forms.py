from django import forms
from .models import Document, Reading, Site, UserFullName

from django.forms import ModelChoiceField

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']

class SiteReadingsForm(forms.ModelForm):
    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select())
    technician = forms.ModelChoiceField(queryset=UserFullName.objects.filter(groups__name='Technician'), widget=forms.Select())

    class Meta:
        model = Reading
        fields = ()

    # Override
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['city'].queryset = City.objects.none()
        #self.fields['country'].queryset = Country.objects.none()
