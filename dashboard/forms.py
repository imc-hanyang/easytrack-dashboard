''' Forms for the dashboard app (validation) '''

# stdlib
from typing import Dict, List, Any
import json

# 3rd party
from django import forms
from easytrack import selectors as slc
from easytrack import models as mdl
from easytrack import wrappers as wrp
from easytrack import utils


class CampaignsForm(forms.Form):
    '''Base form class for extracting easytrack user (django -> easytrack core)'''

    email = forms.EmailField(required=True)
    is_authenticated = forms.BooleanField(required=True)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate user
        if not value['is_authenticated']:
            raise forms.ValidationError('Not authenticated')
        if not slc.find_user(user_id=None, email=value['email']):
            raise forms.ValidationError('Invalid User')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get user
        user = slc.find_user(user_id=None, email=value['email'])
        assert user is not None

        # get campaigns
        campaigns = slc.get_supervisor_campaigns(user=user)
        campaigns.sort(key=lambda x: x.id)

        # return user and campaigns
        return user, campaigns


class CampaignParticipantsForm(forms.Form):
    '''Form for campaign participants request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=True)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate user
        user = slc.find_user(user_id=None, email=value['email'])
        if not user:
            raise forms.ValidationError('Invalid User')

        # Validate campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])
        if not campaign:
            raise forms.ValidationError('Invalid Campaign ID')
        if not slc.is_supervisor(campaign=campaign, user=user):
            raise forms.ValidationError('Not a supervisor of this campaign')
        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get user
        user = slc.find_user(user_id=None, email=value['email'])

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])

        # get participants
        participants = slc.get_campaign_participants(campaign)

        # return user, campaign, and participants
        return user, campaign, participants


class ParticipantDataSourcesForm(forms.Form):
    '''Form for participant data sources request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=True)
    participant_id = forms.IntegerField(required=True)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate user
        user = slc.find_user(user_id=None, email=value['email'])
        if not user:
            raise forms.ValidationError('Invalid User')

        # Validate campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])
        if not campaign:
            raise forms.ValidationError('Invalid Campaign ID')
        if not slc.is_supervisor(campaign=campaign, user=user):
            raise forms.ValidationError('Not a supervisor of this campaign')

        # Validate participant
        participant_user = slc.find_user(
            user_id=value['participant_id'],
            email=None,
        )
        if not participant_user:
            raise forms.ValidationError('Invalid Participant ID')
        if not slc.is_participant(campaign=campaign, user=participant_user):
            raise forms.ValidationError('Not a participant of this campaign')
        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get user
        user = slc.find_user(user_id=None, email=value['email'])

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])

        # get participant
        participant = slc.get_participant(
            campaign,
            slc.find_user(
                user_id=value['participant_id'],
                email=None,
            ))

        # get data source statistics
        data_sources: List[Dict[str, Any]] = []
        participant_stats = wrp.ParticipantStats(participant=participant)
        for data_source in slc.get_campaign_data_sources(campaign=campaign):
            data_source_stats = participant_stats[data_source]
            data_sources.append({
                'id':
                data_source.id,
                'name':
                data_source.name,
                'icon_name':
                data_source.icon_name,
                'configurations':
                data_source.configurations,
                'amount_of_data':
                data_source_stats.amount_of_samples,
                'last_sync_time':
                data_source_stats.last_sync_time,
            })
        data_sources.sort(key=lambda x: x['name'])

        # return user, campaign, participant, and data sources
        return user, campaign, participant, data_sources


class DataRecordsForm(forms.Form):
    '''Form for participant data sources request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=True)
    participant_id = forms.IntegerField(required=True)
    data_source_id = forms.IntegerField(required=True)
    from_timestamp = forms.IntegerField(required=True)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate user
        user = slc.find_user(user_id=None, email=value['email'])
        if not user:
            raise forms.ValidationError('Invalid User')

        # Validate campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])
        if not campaign:
            raise forms.ValidationError('Invalid Campaign ID')
        if not slc.is_supervisor(campaign=campaign, user=user):
            raise forms.ValidationError('Not a supervisor of this campaign')

        # Validate participant
        participant_user = slc.find_user(
            user_id=value['participant_id'],
            email=None,
        )
        if not participant_user:
            raise forms.ValidationError('Invalid Participant ID')
        if not slc.is_participant(campaign=campaign, user=participant_user):
            raise forms.ValidationError('Not a participant of this campaign')

        # Validate data source
        data_source = slc.find_data_source(
            data_source_id=value['data_source_id'])
        if not data_source:
            raise forms.ValidationError('Invalid Data Source ID')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get user
        user = slc.find_user(user_id=None, email=value['email'])

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])

        # get participant
        participant = slc.get_participant(
            campaign,
            slc.find_user(
                user_id=value['participant_id'],
                email=None,
            ))

        # get data source
        data_source = slc.find_data_source(
            data_source_id=value['data_source_id'])

        # get data records
        from_timestamp = utils.millis_to_datetime(value['from_timestamp'])
        data_table = wrp.DataTable(
            participant=participant,
            data_source=data_source,
        )
        data_records: List[Dict[str, Any]] = []
        tmp = data_table.select_next_k(from_ts=from_timestamp, limit=500)
        for i, record in enumerate(tmp):
            ts = utils.datetime_to_str(timestamp=record.ts, js_format=False)
            ts = ts[:ts.rindex(':')]
            value = json.dumps(record.val)

            # 5KB (e.g., binary files)
            if len(value) > 5 * 1024:
                value = f'[ {len(value):,} byte data record ]'

            data_records.append({
                'row': i + 1,
                'timestamp': ts,
                'value': value,
            })
            from_timestamp = record.ts

        # return user, campaign, participant, data source, data records, and last timestamp
        return user, campaign, participant, data_source, data_records, from_timestamp
