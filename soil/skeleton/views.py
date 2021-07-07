from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView, ListView, View, CreateView
from django.utils import timezone
from django.core import management
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from graphs.models import vsw_reading
from .models import Probe, Document, ProbeDiviner, Diviner, Reading, ReadingType, Site, Season, SeasonStartEnd, CriticalDate, CriticalDateType \
, Variety, VarietySeasonTemplate, SiteDescription, Farm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from formtools.wizard.views import SessionWizardView
from django.core import serializers

from django_tables2 import RequestConfig
from django_tables2 import SingleTableView
from .tables import SiteReportTable

import re
import calendar
import numpy as np
import os
import requests
import json
# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm, SiteReadingsForm, SiteSelectionForm, SiteReportReadyForm, DivinerForm, EOYReportForm

import datetime

from dateutil.relativedelta import relativedelta
from .utils import get_title, get_site_season_start_end, process_probe_data, process_irrigation_data, get_current_season, get_previous_season
from dal import autocomplete
TEMPLATES = {"select_crsf": "wizard/season_select.html"}

###
#    probe_diviner_detail actually adds a diviner and probe deviner entry with NO error checking
#    A quick and dirty way to add without using two admin screens for each entry.
#    The probe diviner list aids this adding

def probe_diviner_detail(request):
    if request.method == 'POST':
        diviner_form = DivinerForm(data=request.POST)
        if diviner_form.is_valid():
            logger.debug(str(request.POST['site']))
            new_diviner = diviner_form.save(commit=False)
            new_diviner.created_by = request.user
            new_diviner.save()
            probe = Probe.objects.get(pk=request.POST['probe'])
            pd, created = ProbeDiviner.objects.update_or_create(probe=probe, diviner=new_diviner,
                defaults={ "created_by": request.user })
    else:
        diviner_form = DivinerForm()
    return render(request, 'probe_diviner/detail.html', { 'diviner_form': diviner_form})

class ProbeDivinerListView(ListView):
    queryset = ProbeDiviner.objects.all().select_related('diviner__site')
    context_object_name = 'probe_diviners'
    template_name = 'probe_diviner/list.html'

'''
    RecommendationReadyView:
    Simple view for page to make the reviewed field of Readings true.
    Once reviewed field is true, it becomes avaiable in Graphs API
'''

class RecommendationReadyView(LoginRequiredMixin, CreateView):

    def get(self, request, *args, **kwargs):
        # get todays date
        date = request.GET.get('date')
        if date == None:
            date = datetime.date.today()
        readings = Reading.objects.select_related('site__farm').select_related('site__technician').filter(site__is_active=True, type__name='Probe', date=date).order_by('date')
        return render(request, 'recommendation_ready.html', { 'readings': readings, 'form': SiteReportReadyForm() })

    def post(self, request, *args, **kwargs):
        reviewed = request.POST.getlist('reviewed')
        sites = []
        try:
            key = os.getenv('HORTPLUS_API_KEY')
            api_url = settings.PROPERTIES_API_URL
            api_url = api_url + 'api/send-reports/irrigation'
            logger.debug('post to url ' + api_url)
            site_serialized_data = []
            for review in reviewed:
                reading = Reading.objects.get(id=review)
                # Get site objects from the reading to post to hortplus
                site = Site.objects.get(id=reading.site_id)
                sites.append(site)
                reading.reviewed = True
                reading.save()
                site_serialized_data.append({'id': site.id})
            data = {
                "service": "fruition",
                "sites": site_serialized_data,
            }
            logger.debug(str(data))
            headers = {
                "X-Api-Key": key,
                "Content-Type":"application/json",
                "SeasonalDatabase":"fruition_2020",
                "service":"fruition"}


            r = requests.post(api_url, headers=headers, data=json.dumps(data))
            logger.debug('status_code:' + str(r.status_code))
            if r.status_code == 200:
                logger.debug('response ' + str(r.text))
                ojson = json.loads(r.text)
                messages.info(request, 'Unknown Site IDs: ' + str(ojson['unknown_site_ids']))
                messages.info(request, 'Unknown Users: ' + str(ojson['unknown_users']))
                messages.info(request, 'Users Sent Report: ' + str(ojson['users_sent_report']))
                messages.info(request, 'Users Not Sent Report: ' + str(ojson['users_not_sent_report']))
            else:
                raise Exception("Error processing request:" + str(r.status_code))
        except Exception as e:
            messages.error(request, "Error: " + str(e))
        return render(request, 'recommendation_ready.html', { 'form': SiteReportReadyForm() })

class OnsiteCreateView(LoginRequiredMixin, CreateView):
    model = Site
    form_class = SiteSelectionForm
    template_name = 'onsite_readings.html'

'''
    Ajax call to load previous reading for a site on the onsite web page
'''

def load_onsite_reading(request):
    site_id = request.GET.get('site')
    date = 'No Previous Date'
    meter = 0

    if site_id:
        try:
            reading = Reading.objects.filter(site=site_id).latest()
            logger.debug(str(reading))
            date = reading.date
            meter = reading.meter
        except ObjectDoesNotExist:
            pass
    return JsonResponse({'date' : date, 'meter' : meter})

'''
    Ajax call to process onsite rain and meter readings for a site on the onsite web page
'''

def process_onsite_reading(request):
    site_id = request.GET.get('site')
    date = request.GET.get('date')
    meter = request.GET.get('meter') or 0
    rain = request.GET.get('rain') or None

    try:
        reading_type = ReadingType.objects.get(name='Probe')
        site = Site.objects.get(id=site_id)

        # round rain to one and meter to zero decimals
        meter = round(float(meter))
        reading, created = Reading.objects.update_or_create(site=site, date=date, type=reading_type,
            defaults={"date": date, "type": reading_type, "created_by": request.user, "rain": rain, "meter": meter})
        messages.success(request, 'Saved.')
    except Exception as e:
        messages.error(request, "Error: " + str(e))

    django_messages = []
    for message in messages.get_messages(request):
        django_messages.append({
            "level": message.level,
            "message": message.message,
            "extra_tags": message.tags,
        })

    return JsonResponse({'date' : date, 'meter' : meter, 'rain' : rain, 'messages': django_messages})

"""
    Uses django-autocomplete-light for a Select box for Sites based on Site Number
"""

class SiteAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = SiteDescription.objects.filter(is_active=True).order_by('site_number')

        if self.q:
            qs = qs.filter(site_number__icontains=self.q)
        return qs

"""
    Handles ajax call to display or update Site Note from the main Readings screen
"""

def process_reading_recommendation(request):
    site_id = request.GET.get('site')
    season_id = request.GET.get('season')
    comment = request.GET.get('comment')
    action = request.GET.get('action')

    logger.debug('request:' + str(request))
    logger.debug('action:' + str(action))

    site = Site.objects.get(id=site_id)
    season = Season.objects.get(id=season_id)

    # Some default values
    latest_reading = None
    previous_reading = None
    latest_comment = None
    previous_comment = None

    week_values = {}
    week_start = 0
    week_start_abbr = 'MO'

    dates = get_site_season_start_end(site, season)
    readings = Reading.objects.filter(site=site, type__name='Probe', date__range=(dates.period_from, dates.period_to)).order_by('-date')

    try:
        latest_reading = readings[0]
        latest_comment = latest_reading.comment
    except:
        pass
    try:
        previous_reading = readings[1]
        previous_comment = previous_reading.comment
    except:
        pass

    # If we have a latest comment
    if latest_comment or comment:

        week_start = latest_reading.date.weekday() + 1
        week_start_abbr = calendar.day_abbr[week_start]
        day_value = 0
        water_day_value = 0
        for day in list(calendar.day_abbr):
            logger.debug(day)
            day_value = request.GET.get(day)

            logger.debug('request day value:' + str(day_value))
            column = 'rec_' + str(day)
            if day_value:
                setattr(latest_reading, column, day_value)
            day_value = getattr(latest_reading, column)
            if day_value is None:
                day_value = 0
            week_values[day] = day_value

            water_day_value = round(float(site.application_rate) * float(day_value))
            week_values[day + '-water'] = water_day_value
            if action == 'submit':
                latest_reading.save()

        logger.debug('Day of week to start:' + str(week_start_abbr) + ' values ' + str(week_values)) # Monday is zero
        if action == 'submit':
            logger.debug('Saving comment')
            latest_reading.comment = comment
            latest_reading.save()
        return JsonResponse({ 'comment' : latest_reading.comment, 'week_start_abbr' : week_start_abbr, 'week_start': week_start, 'values' : week_values })
    elif previous_comment:
        logger.debug('No comment for lastest reading so pre-populate')

        week_start = previous_reading.date.weekday() + 1
        week_start_abbr = calendar.day_abbr[week_start]

        day_value = 0
        water_day_value = 0
        for day in list(calendar.day_abbr):

            day_value = request.GET.get(day)

            logger.debug('request day value:' + str(day_value))
            column = 'rec_' + str(day)
            if day_value:
                setattr(previous_reading, column, day_value)
            day_value = getattr(previous_reading, column)
            if day_value is None:
                day_value = 0
            week_values[day] = day_value

            water_day_value = round(float(site.application_rate) * float(day_value))
            week_values[day + '-water'] = water_day_value
        return JsonResponse({ 'comment' : previous_reading.comment, 'week_start_abbr' : week_start_abbr, 'week_start': week_start, 'values' : week_values })
    else:
        logger.debug('No previous reading so provide blanks')
        comment = ""
        return JsonResponse({ 'comment' : comment, 'week_start_abbr' : week_start_abbr, 'week_start': week_start, 'values' : week_values })

def process_site_note(request):
    site_id = request.GET.get('site')
    comment = request.GET.get('comment')
    site = Site.objects.get(id=site_id)
    if comment:
        site.comment = comment
        site.save()
    return JsonResponse({ 'comment' : site.comment })

"""
class SeasonWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        form_data = None
        success_data = None
        try:
            (form_data, success_data) = process_form_data(form_list, self)
        except Exception as e:
            messages.error(self.request, "Error: " + str(e))
        return render(self.request, 'wizard/season_create_data.html', { 'form_data': form_data, 'success_data': success_data })

'''
    From Season Wizard
'''

def process_form_data(form_list, self):
    form_data = [form.cleaned_data for form in form_list]
    success_data = {}

    # Get form parameters
    regions = form_data[0]['region']
    products = form_data[0]['product']
    season = form_data[0]['season']
    multi_year_season = form_data[0]['multi_year_season']
    refill_fullpoint_copy = form_data[0]['refill_fullpoint_copy']
    logger.debug('Form ' + str(form_data[0]))

    # Get sites we are going to work with
    sites = Site.objects.none()
    for region in regions:
        for product in products:
            sites |= Site.objects.filter(farm__address__locality__state=region, product=product)
    logger.debug('Sites to process in Season Wizard:' + str(sites))

    # If multi season, get season start year
    if multi_year_season:
        logger.debug('Season Year Start ' + str(season.formatted_season_start_year))
        season_end_year = season.season_date + relativedelta(years=1)
        logger.debug('Season Year End ' + season_end_year.strftime('%Y'))

    for site in sites:
        # Grap the start and end date types
        site_season_start_date = None
        site_season_end_date = None
        if multi_year_season:
            site_season_start = VarietySeasonTemplate.objects.get(variety__product__site__id=site.id, critical_date_type__name='Start')
            site_season_start_date = site_season_start.season_date
            logger.debug('For ' + str(site) + ' site_season_start_date' + str(site_season_start_date))

        # get variety season TEMPLATES
        templates = VarietySeasonTemplate.objects.filter(variety__product__site__id=site.id)
        for template in templates:
            template_season_date = None
            logger.debug('For ' + str(site) + ' creating crtical date ' + str(template.critical_date_type) + str(template.season_date) + ' to season ' + str(season))



            # Transofrm template.season_date by
            try:
                cd = CriticalDate(
                    site = site,
                    season = season,
                    date = template.season_date,
                    type = template.critical_date_type,
                    created_by = self.request.user
                )
                #cd.save()
                success_data['sites'] = sites
            except Exception as e:
                raise Exception("Cannot create critical date " + str(site) + " because " + str(e))

    if form_data[1]['types_copy']:
        logger.debug('Copying Refill and Full Point Types')

        # Use previous seasons start date as the reading date
        for site in sites:
            dates = get_site_season_start_end(site, previous_season)
    else:
        period_from = form_data[1]['period_from']
        logger.debug('Creating Refill and Full Point Types for season ' + str(season) + ' with reading date of ' + str(period_from))
        for site in sites:
            reading = Reading(
                site = site,
                date = period_from,
                type = 'Refill',
                depth1 = form_data[2]['refill_depth1_value']
            )
            reading.save()
    return (form_data, success_data)
"""

from io import StringIO

@login_required
def index(request):
    if request.method == 'POST':
        out = StringIO()
        try:
            button_clicked = request.POST['button']
            #if button_clicked == 'processreport':
            #    management.call_command('process_report', stdout=out)
            if button_clicked == 'processrootzones':
                management.call_command('processrootzones')
            if button_clicked == 'processmeter':
                management.call_command('processmeter', stdout=out)
            if button_clicked == 'processdailywateruse':
                management.call_command('processdailywateruse', stdout=out)
            if button_clicked == 'processrain':
                management.call_command('processrainirrigation', stdout=out)
            if button_clicked == 'processall':
                management.call_command('processall_readings')
            if button_clicked == 'load-rainfall':
                management.call_command('request_to_hortplus', purpose='process_readings')
        except Exception as e:
            messages.error(request, "Error: " + str(e))

        # For management commands if we want multiple messages to users, we need to sick stdout. (We also have to reserve stdout for messages)
        lines = out.getvalue().splitlines()
        for line in lines:
            messages.warning(request, line)

        messages.success(request, "Successfully ran: " + str(button_clicked))
    return render(request, 'index.html', {})

'''
    Reports
'''

class EOYReportView(LoginRequiredMixin, CreateView):

    def get(self, request, *args, **kwargs):

        return render(request, 'report_eoy.html', { 'form': EOYReportForm() })

def report_season_dates(request):
    season = get_current_season()
    sites = SiteReportTable(Site.objects.filter(is_active=True).filter(~Q(seasonstartend__season=season)))
    return render(request, "report_output.html", {
        "title": "Sites Missing a Season Start and End Date for Season " + season.name,
        "table": sites
    })

def report_missing_reading_types(request):
    missing_sites = Site.objects.none() # Iniliase missing sites to empty queryset object
    try:
        season = get_current_season()
        sites = Site.objects.filter(is_active=True)

        for site in sites:
            dates = get_site_season_start_end(site, season)
            if dates:
                missing_site = Site.objects.filter(is_active=True).filter(~Q(readings__type__name='Refill', readings__date__range=(dates.period_from, dates.period_to))|~Q(readings__type__name='Full Point', readings__date__range=(dates.period_from, dates.period_to)),id=site.id).order_by('site_number')
                if (missing_site):
                    missing_sites |= missing_site # Some great magic to concatenate querysets together
            else:
                messages.warning(request, "Site " + site.name + " has no season start and end dates.")
        sites = SiteReportTable(missing_sites)
        RequestConfig(request).configure(sites)
    except Exception as e:
        sites = SiteReportTable(missing_sites)
        messages.error(request, "Error: " + str(e))
    return render(request, "report_output.html", {
        "title": "Sites Missing a Refill or Full Point Reading Type for Season " + season.name,
        "table": sites
    })

def report_no_meter_reading(request):
    missing_sites = Site.objects.none() # Iniliase missing sites to empty queryset object
    try:
        season = get_current_season()
        sites = Site.objects.filter(is_active=True)

        for site in sites:
            dates = get_site_season_start_end(site, season)
            if dates:
                missing_site = Site.objects.filter(is_active=True, readings__type__name='Probe', readings__meter__isnull=True, readings__date__range=(dates.period_from, dates.period_to)).order_by('site_number').distinct()
                if (missing_site):
                    missing_sites |= missing_site # Some great magic to concatenate querysets together
            else:
                messages.warning(request, "Site " + site.name + " has no season start and end dates.")
        sites = SiteReportTable(missing_sites)
        RequestConfig(request).configure(sites)
    except Exception as e:
        sites = SiteReportTable(missing_sites)
        messages.error(request, "Error: " + str(e))
    return render(request, "report_output.html", {
        "title": "Sites Missing any Meter Reading for Season " + season.name,
        "table": sites
    })

'''
    Page that hosts reports. Click a button to run the query and uses django_tables2 to output data
'''
def weather(request):
    return render(request, 'weather.html', {})

@login_required
def report_home(request):
    if request.method == 'POST':
        try:
            button_clicked = request.POST['button']
            if button_clicked == 'reportEOY':
                url = reverse('report_eoy')
                return HttpResponseRedirect(url)
            if button_clicked == 'reportSeasonDates':
                return HttpResponseRedirect(reverse('report_season_dates'))
            if button_clicked == 'reportMissingReadingTypes':
                return HttpResponseRedirect(reverse('report_missing_reading_types'))
            if button_clicked == 'reportNoMeterReading':
                return HttpResponseRedirect(reverse('report_no_meter_reading'))
        except Exception as e:
            messages.error(request, "Error: " + str(e))
    return render(request, 'report_home.html', {})

#TODO why CreateView and not Template View
class SiteReadingsView(LoginRequiredMixin, CreateView):
    model = Reading
    form_class = SiteReadingsForm
    template_name = 'site_readings.html'

def load_graph(request):
    site_id = request.GET.get('site')
    season_id = request.GET.get('season')
    context = None
    latest = None
    previous = None

    try:
        site = Site.objects.get(id=site_id)
        season = Season.objects.get(id=season_id)

        title = get_title(site_id)
        dates = get_site_season_start_end(site, season)

        readings = Reading.objects.filter(site=site.id, type__name='Probe', date__range=(dates.period_from, dates.period_to)).order_by('-date')
        logger.info(str(readings))
        try:
            latest = readings[0].date
        except:
            pass
        try:
            previous = readings[1].date
        except:
            pass
        logger.debug("Date:" + str(latest))
        logger.debug("Previous:" + str(previous))

        context = {
            'title' : title,
            'site_id' : site_id,
            'date' : latest,
            'previous': previous,
            'period_to': dates.period_to,
            'period_from': dates.period_from
        }
    except Exception as e:
        messages.error(request, "Error with Loading Graph: " + str(e))
    return render(request, 'vsw_percentage.html', context)

def load_sites(request):
    technician_id = request.GET.get('technician')
    farm_id = request.GET.get('farm')

    sites = SiteDescription.objects.filter(Q(technician_id=technician_id)|Q(farm_id=farm_id), is_active=True, )

    # Need to get sites ordered by the latest probe reading date. Which is complicated. There may be a better way then below.
    final_sites = Reading.objects.none()
    for site in sites:
        latest_reading = None
        try:
            latest_reading = Reading.objects.filter(site=site.id, type=1).latest('date')
            final_site = Reading.objects.select_related('site').filter(site__id=site.id, type=1, date=latest_reading.date)
            final_sites |= final_site
        except ObjectDoesNotExist:
            pass

    final_sites = final_sites.order_by('-date')
    return render(request, 'site_dropdown_list_options.html', {'readings':final_sites})

def load_site_readings(request):
    readings = None
    comment = ''
    rainfall_total = 0
    irrigation_total = 0

    try:
        site_id = request.GET.get('site')
        season_id = request.GET.get('season')
        # Get farm and techncian of site
        if site_id:
            title = get_title(site_id)
            try:
                dates = SeasonStartEnd.objects.get(site=site_id, season=season_id)
            except:
                raise Exception("No Season Start and End set up for site.")

            # Using the vsw_readings view in the graph app as it has all the calibrations applied
            readings = vsw_reading.objects.filter(site_id=site_id, date__range=(dates.period_from, dates.period_to)).order_by('-date')
            if readings:
                # Get the last comment
                c = readings.filter().last()
                comment = c.comment

                # Total Rainfall and irrigation
                rainfall_total = readings.aggregate(Sum('rain'))
                irrigation_total = readings.aggregate(Sum('irrigation_mms'))

    except Exception as e:
        messages.error(request, " Error is: " + str(e))
    return render(request, 'site_readings_list.html', {
        'title' : title,
        'readings' : readings,
        'comment' : comment,
        'rainfall' : rainfall_total,
        'irrigation' : irrigation_total,
    })

@login_required
def vsw_percentage(request, site_id, year, month, day):
    template = loader.get_template('vsw_percentage.html')

    context = {
        'site_id' : site_id,
        'year' : year,
        'month' : month,
        'day': day
    }
    return HttpResponse(template.render(context, request))

class UploadReadingsFileView(LoginRequiredMixin, CreateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'upload_readings_file.html', { 'form': DocumentForm() })

    def post(self, request, *args, **kwargs):
        out = StringIO()
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('document')

        if form.is_valid():
            for f in files:
                logger.info('***Saving File:' + str(f))
                form.save()
                try:
                    sites = handle_file(f, request)
                    logger.debug("Sites:" + str(sites))

                    management.call_command('processrootzones', stdout=out, sites=sites)
                    management.call_command('request_to_hortplus', stdout=out, sites=sites)
                    management.call_command('processmeter', stdout=out, sites=sites)
                    management.call_command('processdailywateruse', stdout=out, sites=sites)
                    management.call_command('processrainirrigation', stdout=out, sites=sites)

                except Exception as e:
                    messages.info(request, "info with file: " + str(f) + " info is: " + str(e))
                messages.success(request, "Successfully Uploaded file: " + str(f))
            return redirect('upload_readings_file')
        else:
            logger.info('***Form not valid:' + str(form))



'''
    handle_file - Generic file handler to create a data file as it is uploaded through a web form
'''

def handle_file(f, request):
    # File saved. Now try and process it
    logger.debug('***Processing File:' + str(f))
    type = request.POST['filetype']

    file_data = ""
    try:
        for chunk in f.chunks():
            file_data = file_data + chunk.decode("utf-8")
    except Exception as e:
        logger.info(e)
    finally:
        # Call different handlers
        if type == 'neutron':
            sites = handle_neutron_file(file_data, request)
            return sites
        elif type == 'diviner_7003' or type == 'diviner_7777' or type == 'diviner_953':
            sites = handle_diviner_file(file_data, request, type)
            return sites
        else:
            handle_prwin_file(file_data, request)

'''
    handle_neutron_file

    * Stores data in depthn_count field
'''

def handle_neutron_file(file_data, request):
    logger.info("***Handling Neutron Probe File")

    lines = file_data.split("\n")
    logger.debug("Serial Line:" + lines[1])
    serialfields = lines[1].split(",")
    serialnumber = serialfields[1]
    serialnumber_formatted = serialnumber.lstrip("0")
    logger.debug("Serial Number:" + serialnumber_formatted)

    # Check Serial Number exists and return info message if is not. Then get the serial number unique id
    if not Probe.objects.filter(serial_number=serialnumber_formatted).exists():
        raise Exception("Serial Number:" + serialnumber_formatted + " does not exist.")
    p = Probe.objects.get(serial_number=serialnumber_formatted)
    serial_number_id = p.id

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    readings = []

    for line in lines:
        # If Note, grab the site_id
        note = re.search("^Note,[a-zA-Z0-9_]+", line)
        reading = re.search("^\d.*", line)
        if note:
            logger.debug("***We have a note line:" + line)
            # If not first note line of file
            if any(data):
                readings.reverse() # Neutron Probe files go from deepest to shallowest
                data[key].append(readings)
                readings = []
            site_line = line.split(",")
            site_number = site_line[1].rstrip()
            logger.info("Site Number:" + str(site_number))
        elif reading:
            logger.info("***We have a reading line:" + line)
            reading_line = line.split(",")
            # If first reading for note, we need to get the date and create the key
            if reading_line[0] == "1":
                # Get date part from first depth is fine. Comes in as DD/MM/YY American crap format before we get underscore time component
                date_raw = str(reading_line[11])
                datefields = date_raw.split("_")
                date = datefields[0]
                date_object = datetime.datetime.strptime(date, '%m/%d/%y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')

                key = site_number.rstrip() + "," + date_formatted + "," + "Probe"
                logger.info("Key:" + key)

                if key in data:
                    logger.info("Key exists:")
                else:
                    logger.info("No Key does not exist:")
                    data[key] = []
            if float(reading_line[7]) == 0:
                reading_line[7] = np.nan
            readings.append(float(reading_line[7]))
        else:
            logger.info("Else not valid processing line!"  + line)

    readings.reverse()
    data[key].append(readings) # Always insert last reading
    logger.info("Final Data submitted to process_probe_data:" + str(data))
    sites = process_probe_data(data, serial_number_id, request, 'N')
    return sites

'''
    handle_diviner_file

    * Stores data in depthn field
'''

def handle_diviner_file(file_data, request, type):
    logger.info("***Handling Diviner Probe File")
    # Get probe serial number for type
    probes = type.split("_")
    file_type_sn = probes[1]
    logger.debug("***Serial Number From File Type:" + str(file_type_sn))

    lines = file_data.split("\n")

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    serial_number_id = None
    readings = []
    need_date = True
    site = None

    for line in lines:
        # Site Heading line contains the special Diviner Number
        heading = re.search("^Site.*", line)
        # Seems that a reading line is the only one beginning with a number (day part of date)
        reading = re.search("^\d.*", line)

        if heading:
            logger.debug("***We have a heading line:" + line)
            diviner_fields = line.split(",")
            diviner_number = diviner_fields[1]
            diviner_number_formatted = diviner_number.lstrip()
            logger.debug("Diviner Number Formatted:" + diviner_number_formatted)

            # Get Serial Number and Site Number from Diviner Probe and
            try:
                site = Site.objects.get(diviner__diviner_number=int(diviner_number_formatted), diviner__probediviner__probe__serial_number=int(file_type_sn))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for site.")
            site_number = site.site_number
            logger.info("Site Number:" + str(site_number))

            try:
                probe = Probe.objects.get(serial_number=int(file_type_sn), probediviner__diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a probe/serial number.")
            serial_number_id = probe.id
            logger.info("Serial Number ID:" + str(serial_number_id))

        elif reading:
            logger.info("***We have a reading line:" + line)
            reading_line = line.split(",")

            if need_date:
                # Handle date in dd Month YYYY 24HH:MM:SS format
                date_raw = str(reading_line[0])
                date_object = datetime.datetime.strptime(date_raw, '%d %b %Y %H:%M:%S')
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.info("Date:" + date_formatted)
                key = str(site_number) + "," + date_formatted + "," + "Probe"
                logger.info("Key:" + key)
                data[key] = []
                need_date = False

            # Always remove date as the first element
            reading_line.pop(0)
            logger.info(reading_line)
            reading_array = []
            for reading in reading_line:
                reading = reading.lstrip(' ')
                reading = reading.rstrip()
                if float(reading) == 0:
                    reading = np.nan
                reading_array.append(float(reading))

            data[key].append(reading_array)
        else:
            logger.info("Not a line to process:"  + line)

    logger.info("Final Data:" + str(data))
    sites = process_probe_data(data, serial_number_id, request, 'D')
    return sites

'''
    handle_prwin_file

    * Stores data in depthn field
'''

def handle_prwin_file(file_data, request):
    logger.debug("***Handling PRWIN")
    lines = file_data.split("\n")

    # Use first line to get site number and position of serial number (SN). Between serial number and field 3 (date) will be counts (up to 10)
    header = lines[0].split(",")
    site_number = header[0]
    site = Site.objects.get(site_number=site_number)
    logger.info("Site Number:" + site_number + " Site Name:" + site.name)

    sn_index = header.index('SN')
    logger.info("Serial Number Index:" + str(sn_index))

    # Now get rid of the header
    del lines[0]

    # For refill and full point lines the date is old and mangy. Use the current season start date for the site
    season = get_current_season()
    dates = get_site_season_start_end(site, season)
    season_start_date_formatted = dates.period_from.strftime('%Y-%m-%d')
    logger.info("Season Start Date for Current Season " + str(season_start_date_formatted))
    data = {}
    irrigation_data = {}

    for line in lines:
        reading = re.search("^\d.*", line) # Make sure we have a reading line
        if reading:

            fields = line.split(",")
            reading_type = fields[1]
            logger.info("Type:" + reading_type)
            date_formatted = None
            # We only want 'Probe', 'Full' or 'Refill' reading types
            if reading_type == 'Probe' or reading_type == 'Full' or reading_type == 'Refill':
                # Get date part. Comes in as DD/MM/YYYY or DD-MM-YYYY before we get 'space character' time component
                # Wierdly refill has no date, but comes after full so we can use that date
                date_raw = str(fields[2])

                if date_raw:
                    logger.debug("date raw:" + str(date_raw))
                    datefields = date_raw.split(" ")
                    date = datefields[0]
                    date_object = None
                    hypen = re.search("^\d\d-.*", date)
                    if hypen:
                        date_object = datetime.datetime.strptime(date, '%d-%m-%Y') # American
                    else:
                        date_object = datetime.datetime.strptime(date, '%d/%m/%Y') # American

                    date_formatted = date_object.strftime('%Y-%m-%d')
                    logger.info("Date:" + date_formatted)
                    previous_date = date_formatted
                else:
                    logger.debug("Have to use Season Start Date")
                    date_formatted = season_start_date_formatted

                # Serial Number for PR WIN data is always set to manual. We are just going to get it once and asume all PRWIN readings for the season are from one probe
                p = Probe.objects.get(serial_number='Manual')
                serial_number_id = p.id

                # Create Key
                if reading_type == "Probe":
                    key = site_number + "," + date_formatted + ",Probe"
                elif reading_type == "Full":
                    key = site_number + "," + season_start_date_formatted + ",Full Point"
                elif reading_type == "Refill":
                    key = site_number + "," + season_start_date_formatted + ",Refill"
                else:
                    raise Exception("Unknown reading_type:" + reading_type)
                logger.info("Key:" + key)

                reading_array = []
                irrigation_array = []
                data[key] = []
                irrigation_data[key] = []

                for depth in range(3, sn_index):
                    reading = 0
                    if fields[depth] is not '':
                        reading = float(fields[depth])
                        logger.debug("Reading:" + str(reading))
                        reading_array.append(reading)

                #logger.info("Reading Array:" + str(reading_array))

                # Wierldy enough we make 3 of these arrays to put in data to match nuetron and diviner
                for lap in range(3):
                    data[key].append(reading_array)

                # For PRWIN files we also upload other readings data (already been derived from counts)
                # (SN), 0-100 cm (rz1),0-70 cm (rz2),0-45 cm (rz3),Deficit,ProbeDWU (probe_dwu),EstimatedDWU (estimated_dwu),
                # Rain,Meter,Irrigation(L) (irrigation_litres),Irrigation(mm) (irrigation_litres_mms) ,EffRain1 (effective_rain_1),
                # Effective Rainfall (effective_rainfall) ,EffIrr1 (efflrr1),EffIrr2 (efflrr1), Effective Irrigation (effective_irrigation)

                for value in range(sn_index + 1, sn_index + 16):
                    irrigation = 0.0
                    if fields[value]:
                        irrigation = float(fields[value])
                    logger.info("Irrigation:" + str(irrigation))
                    irrigation_array.append(irrigation)
                irrigation_data[key] = irrigation_array

        # End if we have a reading
    # End loop through lines

    logger.info("Final Data:" + str(data))
    logger.info("irrir array" + str(irrigation_data))
    process_probe_data(data, serial_number_id, request, 'P')
    process_irrigation_data(irrigation_data, serial_number_id, request)
