from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ['description', 'document', 'created_date', 'created_by']
