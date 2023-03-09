''' Forms for the dashboard app (validation) '''

# stdlib
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

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


class CampaignEditorForm(forms.Form):
    '''Form for campaign editor request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=False)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate campaign if campaign_id is provided
        if value['campaign_id']:
            campaign = slc.get_campaign(campaign_id=value['campaign_id'])
            if not campaign:
                raise forms.ValidationError('Invalid Campaign ID')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # return campaign or None
        campaign_id = value.get('campaign_id', None)
        if campaign_id:
            return slc.get_campaign(campaign_id=campaign_id)
        return None


class DatasetInfoForm(forms.Form):
    '''Form for dataset info request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=False)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate campaign if campaign_id is provided
        if value['campaign_id']:
            campaign = slc.get_campaign(campaign_id=value['campaign_id'])
            if not campaign:
                raise forms.ValidationError('Invalid Campaign ID')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])

        # return campaigns
        return campaign


class CampaignResearchersForm(forms.Form):
    '''Form for campaign researchers request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=False)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Validate campaign if campaign_id is provided
        if value['campaign_id']:
            campaign = slc.get_campaign(campaign_id=value['campaign_id'])
            if not campaign:
                raise forms.ValidationError('Invalid Campaign ID')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])

        # return campaigns
        return campaign


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
            timestamp = utils.datetime_to_str(
                timestamp=record.ts,
                js_format=False,
            )
            timestamp = timestamp[:timestamp.rindex(':')]
            value = json.dumps(record.val)

            # 5KB (e.g., binary files)
            if len(value) > 5 * 1024:
                value = f'[ {len(value):,} byte data record ]'

            data_records.append({
                'row': i + 1,
                'timestamp': timestamp,
                'value': value,
            })
            from_timestamp = record.ts

        # return user, campaign, participant, data source, data records, and last timestamp
        return user, campaign, participant, data_source, data_records, from_timestamp


class DataQualityGraphForm(forms.Form):
    '''Form for participant data quality graph request/view validation'''

    email = forms.EmailField(required=True)
    campaign_id = forms.IntegerField(required=True)
    participant_id = forms.IntegerField(required=False)
    data_source_id = forms.IntegerField(required=False)
    plot_date = forms.DateField(required=False)

    def clean(self):
        '''Validate form data'''
        value = super().clean()
        if self.errors:
            return value

        # Campaign ID must be provided
        campaign_id = value.get('campaign_id', None)
        if not campaign_id:
            raise forms.ValidationError('Invalid Campaign ID')

        # Check if campaign_id exists
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])
        if not campaign:
            raise forms.ValidationError('Invalid Campaign ID')

        # Check if user(email) is a supervisor of the campaign
        user = slc.find_user(user_id=None, email=value['email'])
        if not user:
            raise forms.ValidationError('Invalid User')
        if not slc.is_supervisor(campaign=campaign, user=user):
            raise forms.ValidationError('Not a supervisor of this campaign')

        # Check participant_id if provided
        if value.get('participant_id', None):
            participant_user = slc.find_user(user_id=value['participant_id'])
            if not participant_user:
                raise forms.ValidationError('Invalid Participant ID')
            is_participant = slc.is_participant(
                campaign=campaign,
                user=participant_user,
            )
            if not is_participant:
                raise forms.ValidationError(
                    'Not a participant of this campaign')

        # Validate data source if data_source_name is provided
        if value.get('data_source_id', None):
            data_source = slc.find_data_source(
                data_source_id=value['data_source_id'],
                name=None,
            )
            if not data_source:
                raise forms.ValidationError('Invalid Data Source ID')

        return value

    def to_python(self):
        '''Convert form data to python data'''
        value = self.clean()

        # get campaign
        campaign = slc.get_campaign(campaign_id=value['campaign_id'])
        assert campaign is not None

        # get participant
        participant: Optional[mdl.Participant] = None
        if value.get('participant_id', None):
            participant = slc.get_participant(
                campaign=campaign,
                user=slc.find_user(user_id=value['participant_id']),
            )

        # get data source
        data_source: Optional[mdl.DataSource] = None
        if value.get('data_source_id', None):
            data_source = slc.find_data_source(
                data_source_id=value['data_source_id'],
                name=None,
            )

        # get plot date
        plot_date: Optional[datetime] = None
        if value.get('plot_date', None):
            plot_date = value['plot_date']

        # return campaign, participant, data source, and plot date
        return campaign, participant, data_source, plot_date
