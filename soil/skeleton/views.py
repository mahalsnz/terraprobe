from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .forms import DocumentForm

class IndexView(TemplateView):
    template_name = 'index.html'
    #template = loader.get_template('skeleton/index.html')
    #context = {}
    #return HttpResponse(template.render(context, request))

def simple_upload(request):
    template = loader.get_template('simple_upload.html')
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return render(request, 'simple_upload.html', {
            'uploaded_file_url' : uploaded_file_url
        })
    return render(request, 'simple_upload.html')

def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })





'''
from rest_pandas import PandasView
from .models import Reading, Site, ReadingType
from .serializers import ReadingSerializer, SiteSerializer, ReadingTypeSerializer

class GraphView(PandasView):
    def get_queryset(self):
        queryset = Site.objects.filter(id=self.kwargs["pk"])
        return queryset
    serializer_class = SiteSerializer
'''
