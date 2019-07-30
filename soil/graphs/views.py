from django.http import HttpResponse
from django.template import loader

def first_graph(request, site_id):
    template = loader.get_template('graphs/first_graph.html')
    context = {
        'site_id' : site_id,
    }
    return HttpResponse(template.render(context, request))

def vsw_percentage(request, site_id):
    template = loader.get_template('graphs/vsw_percentage.html')
    context = {
        'site_id' : site_id,
    }
    return HttpResponse(template.render(context, request))

def example_graph(request):
    template = loader.get_template('graphs/example_graph.html')
    context = {}
    return HttpResponse(template.render(context, request))
