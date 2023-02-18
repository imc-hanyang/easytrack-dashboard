'''Views for the dashboard app.'''

from typing import List, Tuple, Optional, Dict
from datetime import timedelta as td
import plotly.graph_objects as go
import collections
import mimetypes
import datetime
import zipfile
import plotly
import json
import os
import re
import html

# libs
from wsgiref.util import FileWrapper

import requests
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse

# easytrack
from easytrack import selectors as slc, models
from easytrack import services as svc
from easytrack import wrappers
from easytrack import utils

# app
from dashboard.models import EnhancedDataSource
from dashboard import utils as dutils
from dashboard import forms


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

    # render the participants page
    return render(
        request=request,
        template_name='participants.html',
        context={
            'user': user,
            'campaign': campaign,
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
def handle_researchers_list(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and str(
                request.GET['campaign_id']).isdigit():
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            supervisor = slc.get_supervisor(user=user, campaign=campaign)
            if supervisor:
                if 'targetEmail' in request.GET and 'action' in request.GET and request.GET[
                        'action'] in ['add', 'remove']:
                    targetUser = slc.find_user(
                        user_id=None, email=request.GET['targetEmail'])
                    if targetUser is not None:
                        if request.GET['action'] == 'add':
                            svc.add_supervisor_to_campaign(
                                new_user=targetUser, supervisor=supervisor)
                        elif request.GET['action'] == 'remove':
                            oldSupervisor = slc.get_supervisor(
                                user=targetUser, campaign=campaign)
                            if oldSupervisor is not None and oldSupervisor.user != campaign.owner:
                                svc.remove_supervisor_from_campaign(
                                    oldSupervisor=oldSupervisor)
                            else:
                                return redirect(to='campaigns')
                        else:
                            return redirect(to='campaigns')

                # return new list of campaign's supervisors
                supervisors = list()
                for s in slc.get_campaign_supervisors(campaign=campaign):
                    supervisors.append({
                        'name': s.user.name,
                        'email': s.user.email
                    })
                supervisors.sort(key=lambda x: x['name'])

                return render(
                    request=request,
                    template_name='supervisors.html',
                    context={
                        'title': "%s's researchers" % campaign.name,
                        'campaign': campaign,
                        'researchers': supervisors,
                        'id': user.id,
                        'session_key': user.session_key,
                    },
                )
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_campaign_editor(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if request.method == 'GET':
            # request to open the campaign editor
            all_data_sources = slc.get_all_data_sources()
            if 'edit' in request.GET and 'campaign_id' in request.GET and str(
                    request.GET['campaign_id']).isdigit():
                # edit an existing campaign
                campaign = slc.get_campaign(
                    campaign_id=int(request.GET['campaign_id']))
                if campaign and slc.is_supervisor(user=user,
                                                  campaign=campaign):
                    data_source_infos: List[Dict[str, str]] = list()
                    selected_data_sources = set(
                        slc.get_campaign_data_sources(campaign=campaign))
                    for data_source in slc.get_all_data_sources():
                        data_source_infos.append({
                            'id':
                            data_source.id,
                            'name':
                            data_source.name,
                            'icon_name':
                            data_source.icon_name,
                            'configurations':
                            data_source.configurations,
                            'selected':
                            data_source in selected_data_sources
                        })
                    data_source_infos.sort(key=lambda _key: _key['name'])
                    return render(
                        request=request,
                        template_name='campaign_editor.html',
                        context={
                            'campaign': campaign,
                            'data_sources': data_source_infos,
                        },
                    )
                else:
                    return redirect(to='campaigns')
            else:
                # edit for a new campaign
                new_data_sources = []
                for data_source in all_data_sources:
                    new_data_sources += [{
                        'name': data_source.name,
                        'configurations': data_source.configurations,
                        'icon_name': data_source.icon_name,
                    }]
                new_data_sources.sort(key=lambda _key: _key['name'])
                return render(
                    request=request,
                    template_name='campaign_editor.html',
                    context={'data_sources': new_data_sources},
                )
        elif request.method == 'POST':
            campaign: Optional[models.Campaign] = None
            if 'campaign_id' in request.POST and utils.str_is_numeric(
                    request.POST['campaign_id']) and int(
                        request.POST['campaign_id']) > -1:
                campaign = slc.get_campaign(
                    campaign_id=int(request.POST['campaign_id']))
                if not campaign or not slc.is_supervisor(user=user,
                                                         campaign=campaign):
                    return redirect(to='campaigns')

            if 'name' in request.POST and all(
                    map(
                        lambda s: s in request.POST and utils.is_web_ts(
                            request.POST[s]), ['startTime', 'endTime'])):
                key = 'DATA_SOURCE_'
                new_data_source_names: List[str] = [
                    s[len(key):]
                    for s in filter(lambda s: re.fullmatch(rf'^{key}\w+$', s),
                                    request.POST)
                ]
                icon_names = [
                    s[6:-1] for s in re.findall(
                        pattern=r'href="\w+\.png"',
                        string=requests.get(
                            f'http://{os.getenv(key="STATIC_HOST")}:{os.getenv(key="STATIC_PORT")}/images/data_source/'
                        ).text,
                    )
                ]
                new_data_sources: List[models.DataSource] = list()
                for name in new_data_source_names:
                    new_icon_name = 'miscellaneous.png'
                    for sub in re.findall('[a-zA-Z]+', name):
                        for icon_name in icon_names:
                            if sub.lower() in icon_name:
                                new_icon_name = icon_name
                                break
                    configurations_str = html.unescape(
                        request.POST.get(f'CONFIGURATIONS_{name}', ''))
                    configurations = json.loads(
                        configurations_str.replace(
                            ' ', '')) if configurations_str else {}
                    new_data_sources.append(
                        svc.create_data_source(
                            name=name,
                            icon_name=new_icon_name,
                            configurations=configurations,
                        ))
                if len(new_data_sources) == 0:
                    return redirect(to='campaigns')
                campaign_name = str(request.POST['name'])
                campaign_start_ts = datetime.datetime.fromtimestamp(
                    utils.parse_timestamp_str(
                        request.POST['startTime']).timestamp())
                campaign_end_ts = datetime.datetime.fromtimestamp(
                    utils.parse_timestamp_str(
                        request.POST['endTime']).timestamp())

                if campaign and slc.is_supervisor(user=user,
                                                  campaign=campaign):
                    svc.update_campaign(
                        supervisor=slc.get_supervisor(user=user,
                                                      campaign=campaign),
                        name=campaign_name,
                        start_ts=campaign_start_ts,
                        end_ts=campaign_end_ts,
                        data_sources=new_data_sources,
                    )
                elif not campaign:
                    svc.create_campaign(
                        owner=user,
                        name=campaign_name,
                        start_ts=campaign_start_ts,
                        end_ts=campaign_end_ts,
                        data_sources=new_data_sources,
                    )
                return redirect(to='campaigns')
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_easytrack_monitor(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            all_data_sources = slc.get_campaign_data_sources(campaign=campaign)
            all_participants = slc.get_campaign_participants(campaign=campaign)
            selected_participant = None
            if campaign is not None:
                from_ts = datetime.datetime.now().replace(hour=0,
                                                          minute=0,
                                                          second=0,
                                                          microsecond=0)
                till_ts = from_ts + datetime.timedelta(hours=24)

                if 'plot_date' in request.GET:
                    plot_date_str = str(request.GET['plot_date'])
                    if re.search(r'\d{4}-\d{1,2}-\d{1,2}',
                                 plot_date_str) is not None:
                        year, month, day = plot_date_str.split('-')
                        from_ts = datetime.datetime(year=int(year),
                                                    month=int(month),
                                                    day=int(day),
                                                    hour=0,
                                                    minute=0,
                                                    second=0,
                                                    microsecond=0)
                        till_ts = from_ts + datetime.timedelta(hours=24)

                if 'participant_id' in request.GET and request.GET[
                        'participant_id'].isdigit():
                    selected_user = slc.find_user(user_id=int(
                        request.GET['participant_id']),
                                                  email=None)
                    if selected_user is not None:
                        selected_participant = slc.get_participant(
                            user=selected_user, campaign=campaign)

                WINDOW_SIZE = td(hours=1)  # 1-hour sliding window
                if 'data_source_id' in request.GET and request.GET[
                        'data_source_id'].isdigit():
                    data_source = slc.find_data_source(data_source_id=int(
                        request.GET['data_source_id']),
                                                       name=None)
                    if data_source is not None:
                        hourly_stats = collections.defaultdict(int)
                        # region compute hourly stats
                        for participant in (all_participants
                                            if not selected_participant
                                            or selected_participant.id == 'all'
                                            else [selected_participant]):
                            data_table = wrappers.DataTable(
                                participant=participant,
                                data_source=data_source)
                            ts = from_ts
                            while ts < till_ts:
                                amount = data_table.select_count(
                                    from_ts=ts,
                                    till_ts=ts + WINDOW_SIZE,
                                )
                                hourly_stats[ts.hour] += amount
                                ts += WINDOW_SIZE
                        # endregion

                        plot_data_source = EnhancedDataSource(
                            db_data_source=data_source)
                        # region plot hourly stats
                        x = []
                        y = []
                        max_amount = 10
                        hours = list(hourly_stats.keys())
                        hours.sort()
                        for hour in hours:
                            amount = hourly_stats[hour]
                            if hour < 13:
                                hour = f'{hour} {"pm" if hour == 12 else "am"}'
                            else:
                                hour = f'{hour % 12} pm'
                            x += [hour]
                            y += [amount]
                            max_amount = max(max_amount, amount)
                        fig = go.Figure([go.Bar(x=x, y=y)])
                        fig.update_yaxes(range=[0, max_amount])
                        plot_str = plotly.offline.plot(fig,
                                                       auto_open=False,
                                                       output_type="div")
                        plot_data_source.attach_plot(plot_str=plot_str)
                        # endregion

                        return render(
                            request=request,
                            template_name='dq_completeness.html',
                            context={
                                'title': 'EasyTracker',
                                'campaign': campaign,
                                'plot_date':
                                f'{from_ts.year}-{from_ts.month:02}-{from_ts.day:02}',
                                'participants': all_participants,
                                'plot_participant': selected_participant,
                                'all_data_sources': all_data_sources,
                                'plot_data_source': plot_data_source
                            },
                        )
                    else:
                        return redirect(to='campaigns')
                elif 'data_source_id' not in request.GET or request.GET[
                        'data_source_id'] == 'all':
                    hourly_stats = collections.defaultdict(int)
                    # region compute hourly stats
                    for participant in (all_participants
                                        if selected_participant is None else
                                        [selected_participant]):
                        for data_source in all_data_sources:
                            data_table = wrappers.DataTable(
                                participant=participant,
                                data_source=data_source)
                            ts = from_ts
                            while ts < till_ts:
                                amount = data_table.select_count(
                                    from_ts=ts,
                                    till_ts=ts + WINDOW_SIZE,
                                )
                                hourly_stats[ts.hour] += amount
                                ts += WINDOW_SIZE
                    # endregion

                    plot_data_source = {
                        'name': 'all campaign data sources combined'
                    }
                    # region plot hourly stats
                    x = []
                    y = []
                    max_amount = 10
                    hours = list(hourly_stats.keys())
                    hours.sort()
                    for hour in hours:
                        amount = hourly_stats[hour]
                        if hour < 13:
                            hour = f'{hour} {"pm" if hour == 12 else "am"}'
                        else:
                            hour = f'{hour % 12} pm'
                        x += [hour]
                        y += [amount]
                        max_amount = max(max_amount, amount)
                    fig = go.Figure([go.Bar(x=x, y=y)])
                    fig.update_yaxes(range=[0, max_amount])
                    plot_str = plotly.offline.plot(fig,
                                                   auto_open=False,
                                                   output_type="div")
                    plot_data_source['plot'] = plot_str
                    # endregion

                    return render(
                        request=request,
                        template_name='dq_completeness.html',
                        context={
                            'title': 'EasyTracker',
                            'campaign': campaign,
                            'plot_date':
                            f'{from_ts.year}-{from_ts.month:02}-{from_ts.day:02}',
                            'participants': all_participants,
                            'plot_participant': selected_participant,
                            'all_data_sources': all_data_sources,
                            'plot_data_source': plot_data_source
                        },
                    )
                else:
                    return redirect(to='campaigns')
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_dataset_info(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            if campaign is not None:
                campaign_data_sources = slc.get_campaign_data_sources(
                    campaign=campaign)
                campaign_data_sources.sort(key=lambda x: x.name)
                participants: List[models.User] = [
                    p.user
                    for p in slc.get_campaign_participants(campaign=campaign)
                ]
                participants.sort(key=lambda p: p.id)
                return render(
                    request=request,
                    template_name='dataset_details.html',
                    context={
                        'campaign': campaign,
                        'data_sources': campaign_data_sources,
                        'participants': participants,
                        'id': user.id,
                        'session_key': user.session_key
                    },
                )
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_delete_campaign_api(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            if campaign and slc.is_supervisor(user=user, campaign=campaign):
                svc.delete_campaign(supervisor=slc.get_supervisor(
                    user=user, campaign=campaign))
                return redirect(to='campaigns')
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_download_data_api(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            if campaign and slc.is_supervisor(user=user, campaign=campaign):
                if 'participant_id' in request.GET and utils.str_is_numeric(
                        request.GET['participant_id']):
                    target_user = slc.find_user(user_id=int(
                        request.GET['participant_id']),
                                                email=None)
                    if target_user is not None and slc.is_participant(
                            user=target_user, campaign=campaign):
                        # dump data data
                        dump_filepath = svc.dump_data(
                            participant=slc.get_participant(user=target_user,
                                                            campaign=campaign),
                            data_source=None,
                        )
                        print(f'dump filepath : {dump_filepath}')
                        with open(dump_filepath, 'rb') as r:
                            dump_content = bytes(r.read())
                        os.remove(dump_filepath)

                        # archive the dump content
                        now = datetime.datetime.now()
                        filename = f'easytrack-data-{target_user.email}-{now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                        file_path = utils.get_temp_filepath(filename=filename)
                        fp = zipfile.ZipFile(file_path, 'w',
                                             zipfile.ZIP_STORED)
                        fp.writestr(f'{target_user.email}.csv', dump_content)
                        fp.close()
                        with open(file_path, 'rb') as r:
                            content = r.read()
                        os.remove(file_path)

                        res = HttpResponse(content=content,
                                           content_type='application/x-binary')
                        res['Content-Disposition'] = f'attachment; filename={filename}'
                        return res
                    else:
                        return redirect(to='campaigns')
                else:
                    return redirect(to='campaigns')
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_download_csv_api(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            if campaign and slc.is_supervisor(user=user, campaign=campaign):
                if 'user_id' in request.GET and utils.str_is_numeric(
                        request.GET['user_id']):
                    target_user = slc.find_user(user_id=int(
                        request.GET['user_id']),
                                                email=None)
                    if target_user is not None and slc.is_participant(
                            user=user, campaign=campaign):
                        dump_filepath = svc.dump_data(
                            participant=slc.get_participant(user=user,
                                                            campaign=campaign),
                            data_source=None,
                        )
                    else:
                        return redirect(to='campaigns')
                elif 'data_source_id' in request.GET and utils.str_is_numeric(
                        request.GET['data_source_id']):
                    data_source = slc.find_data_source(data_source_id=int(
                        request.GET['data_source_id']),
                                                       name=None)
                    dump_filepaths: List[Tuple[models.Participant,
                                               str]] = list()
                    if data_source:
                        for participant in slc.get_campaign_participants(
                                campaign=campaign):
                            dump_filepaths.append(
                                (participant,
                                 svc.dump_data(participant=participant,
                                               data_source=data_source)))

                        # archive the dump content
                        now = datetime.datetime.now()
                        filename = f'easytrack-data-{data_source.name}-{now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                        dump_filepath = utils.get_temp_filepath(
                            filename=filename)
                        print(f'dump filepath : {dump_filepath}')
                        fp = zipfile.ZipFile(dump_filepath,
                                             'w',
                                             compression=zipfile.ZIP_DEFLATED,
                                             compresslevel=9)
                        for participant, csv_filepath in dump_filepaths:
                            with open(csv_filepath, 'rb') as r:
                                fp.writestr(zinfo_or_arcname=
                                            f'{participant.user.email}.csv',
                                            data=bytes(r.read()))
                            os.remove(dump_filepath)
                        fp.close()
                    else:
                        return redirect(to='campaigns')
                else:
                    dump_filepaths: List[Tuple[models.Participant,
                                               str]] = list()
                    for participant in slc.get_campaign_participants(
                            campaign=campaign):
                        dump_filepaths.append(
                            (participant,
                             svc.dump_data(participant=participant,
                                           data_source=None)))

                    # archive the dump content
                    now = datetime.datetime.now()
                    filename = f'easytrack-data-{now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                    dump_filepath = utils.get_temp_filepath(filename=filename)
                    print(f'dump filepath : {dump_filepath}')
                    fp = zipfile.ZipFile(dump_filepath,
                                         'w',
                                         compression=zipfile.ZIP_DEFLATED,
                                         compresslevel=9)
                    for participant, csv_filepath in dump_filepaths:
                        with open(csv_filepath, 'rb') as r:
                            fp.writestr(zinfo_or_arcname=
                                        f'{participant.user.email}.csv',
                                        data=bytes(r.read()))
                        os.remove(dump_filepath)
                    fp.close()

                filename = os.path.basename(dump_filepath)
                chunk_size = 8192
                res = StreamingHttpResponse(
                    streaming_content=FileWrapper(open(dump_filepath, 'rb'),
                                                  chunk_size),
                    content_type=mimetypes.guess_type(dump_filepath)[0],
                )
                res['Content-Length'] = os.path.getsize(dump_filepath)
                res['Content-Disposition'] = f'attachment; filename={filename}'
                return res
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['POST'])
def handle_upload_csv_api(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.POST and utils.str_is_numeric(
                request.POST['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.POST['campaign_id']))
            if campaign and slc.is_supervisor(user=user, campaign=campaign):
                if 'user_id' in request.POST and utils.str_is_numeric(
                        request.POST['user_id']):
                    target_user = slc.find_user(user_id=int(
                        request.POST['user_id']),
                                                email=None)
                    if target_user is not None and slc.is_participant(
                            user=user, campaign=campaign):
                        print(request.FILES)
                        pass  # TBD
                    else:
                        return HttpResponse(status=400)
                elif 'data_source_id' in request.POST and utils.str_is_numeric(
                        request.POST['data_source_id']):
                    data_source = slc.find_data_source(data_source_id=int(
                        request.POST['data_source_id']),
                                                       name=None)
                    if data_source:
                        for fname in request.FILES:
                            if dutils.file_is_valid(
                                    data_source=data_source,
                                    fp=request.FILES[fname],
                            ):
                                print(fname, 'is valid')
                            else:
                                print(fname, 'is invalid')
                    else:
                        return HttpResponse(status=400)
                else:
                    return HttpResponse(status=400)
                return HttpResponse(status=200)
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


@login_required
@require_http_methods(['GET'])
def handle_download_dataset_api(request):
    user = slc.find_user(user_id=None, email=request.user.email)
    if user is not None:
        if 'campaign_id' in request.GET and utils.str_is_numeric(
                request.GET['campaign_id']):
            campaign = slc.get_campaign(
                campaign_id=int(request.GET['campaign_id']))
            if campaign and slc.is_supervisor(user=user, campaign=campaign):
                dump_filepaths: List[Tuple[models.Participant, str]] = list()
                for participant in slc.get_campaign_participants(
                        campaign=campaign):
                    dump_filepaths.append(
                        (participant,
                         svc.dump_data(participant=participant,
                                       data_source=None)))

                # archive the dump content
                now = datetime.datetime.now()
                filename = f'easytrack-data-{now.month}-{now.day}-{now.year} {now.hour}-{now.minute}.zip'
                dump_filepath = utils.get_temp_filepath(filename=filename)
                print(f'dump filepath : {dump_filepath}')
                fp = zipfile.ZipFile(dump_filepath,
                                     'w',
                                     compression=zipfile.ZIP_DEFLATED,
                                     compresslevel=9)
                for participant, csv_filepath in dump_filepaths:
                    with open(csv_filepath, 'rb') as r:
                        fp.writestr(
                            zinfo_or_arcname=f'{participant.user.email}.csv',
                            data=bytes(r.read()))
                    os.remove(dump_filepath)
                fp.close()

                filename = os.path.basename(dump_filepath)
                chunk_size = 8192
                res = StreamingHttpResponse(
                    streaming_content=FileWrapper(open(dump_filepath, 'rb'),
                                                  chunk_size),
                    content_type=mimetypes.guess_type(dump_filepath)[0],
                )
                res['Content-Length'] = os.path.getsize(dump_filepath)
                res['Content-Disposition'] = f'attachment; filename={filename}'
                return res
            else:
                return redirect(to='campaigns')
        else:
            return redirect(to='campaigns')
    else:
        logout(request=request)
        return redirect(to='login')


def handle_google_verification(request):
    return render(request=request, template_name='google-site.html')
