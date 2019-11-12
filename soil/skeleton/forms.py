from django import forms
from .models import Document, Site, UserFullName
#from django.contrib.auth.models import User
from django.forms import ModelChoiceField

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']

class SelectorForm(forms.Form):

    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs={"onChange":'submit()'}))
    #technician = forms.ModelChoiceField(queryset=UserFullName.objects.filter(groups__name='Technician'), widget=forms.Select(attrs={"onChange":'submit()'}))
