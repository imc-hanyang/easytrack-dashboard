'''Views for the dashboard app.'''

# stdlib
from typing import Dict, Optional
from datetime import timedelta
from datetime import datetime
import collections

# 3rd party
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from easytrack import selectors as slc
from easytrack import models as mdl
from easytrack import wrappers
from easytrack import utils
import plotly.graph_objects as go
import plotly

# local
from dashboard import forms


def handle_google_verification(request):
    '''Renders google-site.html (for google site verification)'''
    return render(request=request, template_name='google-site.html')


@require_http_methods(['GET'])
def login(request):
    '''Renders login page.'''

    # user is not authenticated -> render login page
    if not request.user.is_authenticated:
        return render(
            request=request,
            template_name='login.html',
            context={'title': 'Authentication'},
        )

    # user is authenticated -> assert that user is valid
    assert slc.find_user(user_id=None, email=request.user.email) is not None

    # user is authenticated -> redirect to campaigns page
    return redirect(to='campaigns')


@login_required
@require_http_methods(['GET'])
def campaigns(request):
    '''Renders campaigns page.'''

    # validate the form
    form = forms.CampaignsForm({
        'email':
        request.user.email,
        'is_authenticated':
        request.user.is_authenticated,
    })
    if not form.is_valid():
        logout(request)  # invalid user -> invalidate session (weird)
        return redirect(to='handle_login')
    user, campaigns = form.to_python()

    # render the campaigns page
    return render(
        request=request,
        template_name='campaigns.html',
        context={
            'user': user,
            'campaigns': campaigns,
        },
    )


@login_required
@require_http_methods(['GET'])
def participants(request):
    '''Renders participants page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.CampaignParticipantsForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    user, campaign, participants = form.to_python()

    # get campaign participant statistics
    participants_stats = []
    for participant in participants:
        stats = wrappers.ParticipantStats(participant=participant)
        participants_stats.append({
            'participant_id': participant.user.id,
            'participant_name': participant.user.name,
            'participant_email': participant.user.email,
            'participation_day': stats.participation_duration,
            'amount_of_data': stats.amount_of_data,
            'last_heartbeat_time': participant.last_heartbeat_ts,
            'last_sync_time': stats.last_sync_ts,
        })
    participants_stats.sort(key=lambda x: x['participant_id'])

    # flag if user is joined as participant
    joined_as_participant = slc.is_participant(campaign=campaign, user=user)

    # render the participants page
    return render(
        request=request,
        template_name='participants.html',
        context={
            'user': user,
            'campaign': campaign,
            'joined_as_participant': joined_as_participant,
            'participants_stats': participants_stats,
        },
    )


@login_required
@require_http_methods(['GET'])
def data_sources(request):
    '''Renders data sources page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.ParticipantDataSourcesForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    user, campaign, participant, data_source_stats = form.to_python()

    # render the data sources page
    return render(
        request=request,
        template_name='data_source_stats.html',
        context={
            'user': user,
            'campaign': campaign,
            'participant': participant.user,
            'data_sources': data_source_stats,
        },
    )


@login_required
@require_http_methods(['GET'])
def data_records(request):
    '''Renders (raw) data records page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.DataRecordsForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    user, campaign, participant, data_source, data_records, last_timestamp = form.to_python(
    )

    return render(
        request=request,
        template_name='data_records.html',
        context={
            'user': user,
            'campaign': campaign,
            'participant': participant.user,
            'data_source': data_source,
            'data_records': data_records,
            'last_timestamp': utils.datetime_to_millis(last_timestamp),
        },
    )


@login_required
@require_http_methods(['GET'])
def campaign_editor(request):
    '''Renders campaign editor page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.CampaignEditorForm(form_data)
    campaign: Optional[mdl.Campaign] = None
    if form.is_valid():
        campaign = form.to_python()

    # mark selected data sources
    selected_data_sources: Dict[str, bool] = {}
    if campaign is not None:
        for data_source in slc.get_campaign_data_sources(campaign=campaign):
            selected_data_sources[data_source.name] = True

    # get data sources
    data_sources = []
    for data_source in slc.get_all_data_sources():
        columns = slc.get_data_source_columns(data_source=data_source)
        data_sources.append({
            'name':
            data_source.name,
            'selected':
            selected_data_sources.get(data_source.name, False),
            'columns':
            ', '.join([x.name for x in columns]),
        })

    # prepare context for rendering
    context = {'data_sources': data_sources}
    if campaign is not None:
        context['campaign'] = campaign

    # render the campaign editor page
    return render(
        request=request,
        template_name='campaign_editor.html',
        context=context,
    )


@login_required
@require_http_methods(['GET'])
def dataset_info(request):
    '''Renders dataset info page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.DatasetInfoForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    campaign = form.to_python()

    # get data sources
    data_sources = []
    for data_source in slc.get_campaign_data_sources(campaign=campaign):
        columns = slc.get_data_source_columns(data_source=data_source)
        data_sources.append({
            'id': data_source.id,
            'name': data_source.name,
            'columns': ', '.join([x.name for x in columns]),
        })

    # get participants
    participants = slc.get_campaign_participants(campaign=campaign)

    return render(
        request=request,
        template_name='dataset_details.html',
        context={
            'campaign': campaign,
            'data_sources': data_sources,
            'participants': participants,
        },
    )


@login_required
@require_http_methods(['GET'])
def manage_researchers(request):
    '''Renders dataset info page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.CampaignResearchersForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    campaign = form.to_python()

    # get supervisors / researchers
    supervisors = list(slc.get_campaign_supervisors(campaign=campaign))

    return render(
        request=request,
        template_name='supervisors.html',
        context={
            'campaign': campaign,
            'data_sources': data_sources,
            'supervisors': supervisors,
        },
    )


@login_required
@require_http_methods(['GET'])
def dq_monitor(request):
    '''Renders data quality monitor page.'''

    # validate the form
    form_data = request.GET.copy()
    form_data['email'] = request.user.email
    form = forms.DataQualityGraphForm(form_data)
    if not form.is_valid():
        return redirect(to='campaigns')
    campaign, plot_participant, plot_data_source, plot_date = form.to_python()

    # all data sources and participants
    all_data_sources = slc.get_campaign_data_sources(campaign=campaign)
    all_participants = slc.get_campaign_participants(campaign=campaign)

    # get data sources of interest
    if plot_data_source is not None:
        data_sources = [plot_data_source]
    else:
        data_sources = all_data_sources

    # get participants of interest
    if plot_participant is not None:
        participants = [plot_participant]
    else:
        participants = all_participants

    # establish time range by checking plot_date
    if plot_date is not None:
        from_ts = datetime.combine(plot_date, datetime.min.time())
        till_ts = from_ts + timedelta(hours=24)
    else:
        from_ts = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        till_ts = from_ts + timedelta(hours=24)

    # compute hourly stats
    hourly_stats = collections.defaultdict(int)
    window_size = timedelta(hours=1)  # 1-hour sliding window
    for participant in participants:
        for data_source in data_sources:
            # get data table
            data_table = wrappers.DataTable(participant=participant,
                                            data_source=data_source)

            # slide through the time range and compute hourly stats
            timestamp = from_ts
            while timestamp < till_ts:
                amount = data_table.select_count(
                    from_ts=timestamp,
                    till_ts=timestamp + window_size,
                )
                hourly_stats[timestamp.hour] += amount
                timestamp += window_size

    # prepare hourly stats plot
    x_vals, y_vals, max_amount = [], [], 10
    for hour in sorted(hourly_stats.keys()):
        # attach am/pm suffix for readability
        if hour < 13:
            hour = f'{hour} {"pm" if hour == 12 else "am"}'
        else:
            hour = f'{hour % 12} pm'

        # append x and y values, and update y axis range
        x_vals.append(hour)
        y_vals.append(hourly_stats[hour])
        max_amount = max(max_amount, amount)

    # prepare plotly plot and attach it to the data source
    fig = go.Figure([go.Bar(x=x_vals, y=y_vals)])
    fig.update_yaxes(range=[0, max_amount])
    completeness_plot_str = plotly.offline.plot(
        fig,
        auto_open=False,
        output_type="div",
    )

    plot_date_str = f'{from_ts.year}-{from_ts.month:02}-{from_ts.day:02}'
    return render(
        request=request,
        template_name='dq_monitor.html',
        context={
            'title': 'EasyTracker',
            'campaign': campaign,
            'plot_date': plot_date_str,
            'participants': all_participants,
            'plot_participant': plot_participant,
            'all_data_sources': all_data_sources,
            'plot_data_source': plot_data_source,
            'completeness_plot': completeness_plot_str,
        },
    )
