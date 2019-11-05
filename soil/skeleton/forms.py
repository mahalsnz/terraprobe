from django import forms
from .models import Document, Site
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']

class UserModelChoiceField(forms.ModelChoiceField):
    """
    Extend ModelChoiceField for users so that the choices are
    listed as 'first_name last_name (username)' instead of just
    'username'.

    """
    def label_from_instance(self, obj):
        return "%s (%s)" % (obj.get_full_name(), obj.username)

class SelectorForm(forms.Form):
    #site = forms.CharField(label='Site', max_length=100)to_field_name="id",
    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs={"onChange":'submit()'}))
    technician = forms.UserModelChoiceField(queryset=User.objects.filter(groups__name='Technician'), widget=forms.Select(attrs={"onChange":'submit()'}))
    #days = forms.ModelChoiceField(queryset=Day.objects.all(), widget=forms.Select(attrs={"onChange":'refresh()'}))

    class Meta:
        model = Site
        fields = ['name']
