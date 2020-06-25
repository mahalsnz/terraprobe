from django.http import HttpResponse
from django.template import loader

def customer_weekly(request, site_id):
    template = loader.get_template('customer_weekly.html')
    context = {
        'site_id' : site_id,
    }
    return HttpResponse(template.render(context, request))
