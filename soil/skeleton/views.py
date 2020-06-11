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
from graphs.models import vsw_reading
from .models import Probe, Reading, ReadingType, Site, Season, SeasonStartEnd, CriticalDate, CriticalDateType, Variety, VarietySeasonTemplate, SiteDescription
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from formtools.wizard.views import SessionWizardView

from django_tables2 import RequestConfig
from django_tables2 import SingleTableView
from .tables import SiteReportTable

import re
import requests
import calendar

# Get an instance of a logger
import logging
logger = logging.getLogger(__name__)

from .forms import DocumentForm, SiteReadingsForm, SiteSelectionForm

from datetime import datetime
from dateutil.relativedelta import relativedelta
from .utils import get_site_season_start_end, process_probe_data, process_irrigation_data, get_current_season, get_previous_season
from dal import autocomplete
TEMPLATES = {"select_crsf": "wizard/season_select.html"}

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
    meter = request.GET.get('meter') or None
    rain = request.GET.get('rain') or None

    try:
        reading_type = ReadingType.objects.get(name='Probe')
        site = Site.objects.get(id=site_id)
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

class SiteAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        #if not self.request.user.is_authenticated():
        #    return Site.objects.none()

        qs = SiteDescription.objects.all()

        if self.q:
            qs = qs.filter(site_number__icontains=self.q)

        return qs

'''
    Handles ajax call to display or update site note from the main Readings screen
'''

def process_reading_recommendation(request):
    site_id = request.GET.get('site')
    season_id = request.GET.get('season')
    comment = request.GET.get('comment')

    site = Site.objects.get(id=site_id)
    season = Season.objects.get(id=season_id)

    logger.debug('Application Rate:' + str(site.application_rate))

    dates = get_site_season_start_end(site, season)
    reading = Reading.objects.filter(site=site, type__name='Probe', date__range=(dates.period_from, dates.period_to)).latest('date')

    week_start = reading.date.weekday() + 1
    week_start_abbr = calendar.day_abbr[week_start]
    week_values = {}
    day_value = 0
    water_day_value = 0
    for day in list(calendar.day_abbr):
        logger.debug(day)
        day_value = request.GET.get(day)

        logger.debug('request day value:' + str(day_value))
        column = 'rec_' + str(day)
        if day_value:
            setattr(reading, column, day_value)
        day_value = getattr(reading, column)
        if day_value is None:
            day_value = 0
        week_values[day] = day_value

        water_day_value = round(float(site.application_rate) * float(day_value))
        week_values[day + '-water'] = water_day_value
        reading.save()

    logger.debug('Day of week to start:' + str(week_start_abbr) + ' values ' + str(week_values)) # Monday is zero
    if comment:
        reading.comment = comment
        reading.save()
    return JsonResponse({ 'comment' : reading.comment, 'week_start_abbr' : week_start_abbr, 'week_start': week_start, 'values' : week_values })

def process_site_note(request):
    site_id = request.GET.get('site')
    comment = request.GET.get('comment')
    site = Site.objects.get(id=site_id)
    if comment:
        site.comment = comment
        site.save()
    return JsonResponse({ 'comment' : site.comment })

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

from io import StringIO

@login_required
def index(request):
    if request.method == 'POST':
        out = StringIO()
        try:
            button_clicked = request.POST['button']
            if button_clicked == 'processrootzones':
                management.call_command('processrootzones')
            if button_clicked == 'processmeter':
                management.call_command('processmeter', stdout=out)
            if button_clicked == 'processdailywateruse':
                management.call_command('processdailywateruse')
            if button_clicked == 'processrain':
                management.call_command('processrain')
            if button_clicked == 'processall':
                management.call_command('processall_readings')
            if button_clicked == 'load-rainfall':
                management.call_command('request_to_hortplus')
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

def report_season_dates(request):
    season = get_current_season()
    sites = SiteReportTable(Site.objects.filter(~Q(seasonstartend__season=season)))
    return render(request, "report_output.html", {
        "title": "Sites Missing a Season Start and End Date for Season " + season.name,
        "table": sites
    })

def report_missing_reading_types(request):
    season = get_current_season()
    sites = Site.objects.all()
    missing_sites = Site.objects.none() # Iniliase missing sites to empty queryset object

    for site in sites:
        dates = get_site_season_start_end(site, season)
        if dates:
            missing_site = Site.objects.filter(~Q(readings__type__name='Refill', readings__date__range=(dates.period_from, dates.period_to))|~Q(readings__type__name='Full Point', readings__date__range=(dates.period_from, dates.period_to)),id=site.id).order_by('site_number')
            if (missing_site):
                missing_sites |= missing_site # Some great magic to concatenate querysets together
        else:
            messages.warning(request, "Site " + site.name + " has no season start and end dates.")
    sites = SiteReportTable(missing_sites)
    RequestConfig(request).configure(sites)
    return render(request, "report_output.html", {
        "title": "Sites Missing a Refill or Full Point Reading Type for Season " + season.name,
        "table": sites
    })

def report_no_meter_reading(request):
    season = get_current_season()
    sites = Site.objects.all()
    missing_sites = Site.objects.none()

    for site in sites:
        dates = get_site_season_start_end(site, season)
        if dates:
            missing_site = Site.objects.filter(readings__type__name='Probe', readings__meter__isnull=True, readings__date__range=(dates.period_from, dates.period_to)).order_by('site_number').distinct()
            if (missing_site):
                missing_sites |= missing_site # Some great magic to concatenate querysets together
        else:
            messages.warning(request, "Site " + site.name + " has no season start and end dates.")
    sites = SiteReportTable(missing_sites)
    RequestConfig(request).configure(sites)
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
            if button_clicked == 'reportSeasonDates':
                return HttpResponseRedirect(reverse('report_season_dates'))
            if button_clicked == 'reportMissingReadingTypes':
                return HttpResponseRedirect(reverse('report_missing_reading_types'))
            if button_clicked == 'reportNoMeterReading':
                return HttpResponseRedirect(reverse('report_no_meter_reading'))
        except Exception as e:
            messages.error(request, "Error: " + str(e))
    return render(request, 'report_home.html', {})

'''
class CreateSeasonStartEndView(LoginRequiredMixin, CreateView):
    def get_initial(self, *args, **kwargs):
        initial = super(CreateSeasonStartEndView, self).get_initial(**kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, 'season_start_end.html', { 'form': SeasonStartEndForm() })

    def post(self, request, *args, **kwargs):
        try:
            form = SeasonStartEndForm(request.POST)
            logger.debug(request)
            # for a crop and region get all of those sites
            region = request.POST['region']
            crop = request.POST.getlist('crop')
            season = request.POST['season']
            logger.debug(crop)
            sites = Site.objects.filter(farm__address__locality__state=region, crop=crop)

            if sites:
                # create a couple of start and end critical date critical_date_types
                start_type = CriticalDateType.objects.get(name='Start')
                end_type = CriticalDateType.objects.get(name='End')
                current_user = request.user

                for site in sites:
                    # If we don't already have a season start end we insert, we don't update and existing one
                    exists = SeasonStartEnd.objects.filter(site=site.id, season=season).count()
                    logger.debug(site.name + " has " + str(exists))
                    if exists:
                        logger.debug('Not updating')
                        messages.warning(request, site.name + " already has a start and end date for that season")
                    else:
                        cd = CriticalDate(
                            site = site,
                            season_id = season,
                            date = request.POST['period_from'],
                            type = start_type,
                            created_by = current_user
                        )
                        cd.save()
                        cd = CriticalDate(
                            site = site,
                            season_id = season,
                            date = request.POST['period_to'],
                            type = end_type,
                            created_by = current_user
                        )
                        cd.save()
                        logger.debug('Inserting Season start end records')
                        messages.success(request, "Successfully inserted start and end dates for " + site.name)
            else:
                messages.warning(request, 'No sites in region for that crop')
        except Exception as e:
            messages.error(request, "Error: " + str(e))
        return redirect('season_start_end')
'''

#TODO why CreateView and not Template View
class SiteReadingsView(LoginRequiredMixin, CreateView):
    model = Reading
    form_class = SiteReadingsForm
    template_name = 'site_readings.html'

def load_graph(request):
    site_id = request.GET.get('site')
    season_id = request.GET.get('season')
    context = None

    try:
        site = Site.objects.get(id=site_id)
        season = Season.objects.get(id=season_id)
        dates = get_site_season_start_end(site, season)

        readings = Reading.objects.filter(site=site.id, type__name='Probe', date__range=(dates.period_from, dates.period_to)).order_by('-date')
        logger.info(str(readings))
        try:
            latest = readings[0].date
        except:
            raise Exception("No Reading for Site and Season")
        try:
            previous = readings[1].date
        except:
            raise Exception("No Previous Reading for Site and Season")
        logger.debug("Date:" + str(latest))
        logger.debug("Previous:" + str(previous))

        context = {
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
    sites = Site.objects.filter(Q(technician_id=technician_id)|Q(farm_id=farm_id)).order_by('name')
    return render(request, 'site_dropdown_list_options.html', {'sites':sites})

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
                irrigation_total = readings.aggregate(Sum('irrigation_litres'))
    except Exception as e:
        messages.error(request, " Error is: " + str(e))
    return render(request, 'site_readings_list.html', {
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
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('document')

        if form.is_valid():
            for f in files:
                logger.info('***Saving File:' + str(f))
                form.save()
                try:
                    handle_file(f, request)
                    messages.success(request, "Successfully Uploaded file: " + str(f))
                except Exception as e:
                    messages.info(request, "info with file: " + str(f) + " info is: " + str(e))
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
            handle_neutron_file(file_data, request)
        elif type == 'diviner':
            handle_diviner_file(file_data, request)
        else:
            handle_prwin_file(file_data, request)

'''
    handle_neutron_file

    * Stores data in depthn_count field
'''

def handle_neutron_file(file_data, request):
    logger.debug("***Handling Neutron")
    # process
    lines = file_data.split("\n")
    logger.info("Serial Line:" + lines[1])
    serialfields = lines[1].split(",")
    serialnumber = serialfields[1]
    serialnumber_formatted = serialnumber.lstrip("0")
    logger.info("Serial Number:" + serialnumber_formatted)

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
                date_object = datetime.strptime(date, '%m/%d/%y') # American
                date_formatted = date_object.strftime('%Y-%m-%d')

                key = site_number.rstrip() + "," + date_formatted + "," + "Probe"
                logger.info("Key:" + key)

                if key in data:
                    logger.info("Key exists:")
                else:
                    logger.info("No Key does not exist:")
                    data[key] = []

            readings.append(float(reading_line[7]))
        else:
            logger.info("Else not valid processing line!"  + line)

    data[key].append(readings) # Always insert last reading
    logger.info("Final Data submitted to process_probe_data:" + str(data))
    process_probe_data(data, serial_number_id, request, 'N')

'''
    handle_diviner_file

    * Stores data in depthn field
'''

def handle_diviner_file(file_data, request):
    logger.info("***Handling Diviner")
    lines = file_data.split("\n")

    # Variable for loop
    data = {}
    date_formatted = None
    site_number = None
    serial_number_id = None
    readings = []
    need_date = True

    for line in lines:
        # Site Heading line contains the special Diviner Number
        heading = re.search("^Site.*", line)
        # Seems that a reading line is the only one beginning with a number (day part of date)
        reading = re.search("^\d.*", line)

        if heading:
            logger.info("***We have a heading line:" + line)
            diviner_fields = line.split(",")
            diviner_number = diviner_fields[1]
            diviner_number_formatted = diviner_number.lstrip()
            logger.info("Diviner Number Formatted:" + diviner_number_formatted)

            # Get Serial Number and Site Number from Diviner Probe and
            try:
                site = Site.objects.get(diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a site.")
            site_number = site.site_number
            logger.info("Site Number:" + site_number)

            try:
                sn = Probe.objects.get(probediviner__diviner__diviner_number=int(diviner_number_formatted))
            except:
                raise Exception("Diviner Number:" + diviner_number_formatted + " not set up for a probe/serial number.")
            serial_number_id = sn.id
            logger.info("Serial Number ID:" + str(serial_number_id))

        elif reading:
            logger.info("***We have a reading line:" + line)
            reading_line = line.split(",")

            if need_date:
                # Handle date in dd Month YYYY 24HH:MM:SS format
                date_raw = str(reading_line[0])
                date_object = datetime.strptime(date_raw, '%d %b %Y %H:%M:%S')
                date_formatted = date_object.strftime('%Y-%m-%d')
                logger.info("Date:" + date_formatted)
                key = site_number + "," + date_formatted + "," + "Probe"
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
                reading_array.append(float(reading))

            data[key].append(reading_array)
        else:
            logger.info("Not a line to process:"  + line)

    logger.info("Final Data:" + str(data))
    process_probe_data(data, serial_number_id, request, 'D')

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
                    logger.info("dr" + str(date_raw))
                    datefields = date_raw.split(" ")
                    date = datefields[0]
                    date_object = None
                    hypen = re.search("^\d\d-.*", date)
                    if hypen:
                        date_object = datetime.strptime(date, '%d-%m-%Y') # American
                    else:
                        date_object = datetime.strptime(date, '%d/%m/%Y') # American

                    date_formatted = date_object.strftime('%Y-%m-%d')
                    logger.info("Date:" + date_formatted)
                    previous_date = date_formatted
                else:
                    logger.debug("Have to use Previous Date")
                    date_formatted = previous_date

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
                    reading = float(fields[depth])
                    logger.info("Reading:" + str(reading))
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
