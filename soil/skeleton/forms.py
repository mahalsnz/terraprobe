from django import forms
from .models import Document, Site
from django.forms import ModelChoiceField

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']

class SelectorForm(forms.Form):
    #site = forms.CharField(label='Site', max_length=100)to_field_name="id",
    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs={"onChange":'submit()'}))
    #days = forms.ModelChoiceField(queryset=Day.objects.all(), widget=forms.Select(attrs={"onChange":'refresh()'}))

    class Meta:
        model = Site
        fields = ['name']
