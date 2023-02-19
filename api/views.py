''' Views for the API app. '''

# stdlib
from os import getenv
from time import time_ns
from typing import List
from datetime import datetime

# 3rd party
import pandas as pd

# django
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout

# django rest framework
from rest_framework import generics, permissions
from rest_framework import serializers
from rest_framework import response, status
from rest_framework.exceptions import ValidationError

# google auth
from google.auth.transport import requests as oauth_requests
from google.oauth2 import id_token

# easytrack
from easytrack import selectors as slc
from easytrack import services as svc
from easytrack import models as mdl
from easytrack import utils as et_utils


class LoginGoogle(generics.GenericAPIView):
    '''Login using Google OAuth.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for LoginGoogle.'''

        id_token = serializers.CharField(required=True, allow_blank=False)

        def validate(self, attrs):
            '''Validate the input data.'''
            validated = super().validate(attrs)

            # verify the id_token (google auth)
            google_id_details = id_token.verify_oauth2_token(
                id_token=validated['id_token'],
                request=oauth_requests.Request(),
            )
            valid_iss = ['accounts.google.com', 'https://accounts.google.com']
            if google_id_details['iss'] not in valid_iss:
                raise ValidationError('Invalid id_token issuer')

            return validated

    class OutputSerializer(serializers.Serializer):
        session_key = serializers.CharField()

    http_method_names = ['post']
    serializer_class = InputSerializer

    def post(self, request, *args, **kwargs):
        '''POST for Google oAuth login.'''

        serializer = LoginGoogle.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # get google id details
        google_id_details = id_token.verify_oauth2_token(
            id_token=serializer.validated_data['idToken'],
            request=oauth_requests.Request(),
        )
        email, name = google_id_details['email'], google_id_details['name']

        # get django user
        if User.objects.filter(email=email).exists():
            # existing user
            user = User.objects.get(email=email)
        else:
            # new user
            user = User.objects.create_user(
                username=email,
                first_name=name,
                email=email,
                password=email,
            )

        # authenticate the user (creates session for further requests)
        authenticate(username=email, password=email)
        login(
            request=request,
            user=user,
            backend='django.contrib.auth.backends.ModelBackend',
        )

        # easytrack (core) user
        user = slc.find_user(user_id=None, email=email)
        if user is None:
            session_key = et_utils.md5(value=f'{email}{time_ns()}')
            user = svc.create_user(
                email=email,
                name=name,
                session_key=session_key,
            )
        else:
            session_key = user.session_key

        # return session key
        serializer = LoginGoogle.OutputSerializer(instance={
            'session_key': session_key,
        })
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LoginTest(generics.GenericAPIView):
    '''Login using test account.'''

    class OutputSerializer(serializers.Serializer):
        '''Output serializer for LoginTest.'''
        session_key = serializers.CharField()

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        '''POST for test account login.'''

        # get test account credentials from .env
        email, name = getenv('TEST_ACCOUNT_EMAIL'), getenv('TEST_ACCOUNT_NAME')

        # get django user
        if User.objects.filter(email=email).exists():
            # existing user
            user = User.objects.get(email=email)
        else:
            # new user
            user = User.objects.create_user(
                username=email,
                first_name=name,
                email=email,
                password=email,
            )

        # authenticate request with user's credentials
        authenticate(
            request=request,
            username=email,
            password=email,
        )
        # login the user (creates session for further requests)
        login(
            request=request,
            user=user,
            backend='django.contrib.auth.backends.ModelBackend',
        )

        # easytrack (core) user
        user = slc.find_user(user_id=None, email=email)
        if user is None:
            session_key = et_utils.md5(value=f'{email}{time_ns()}')
            user = svc.create_user(
                email=email,
                name=name,
                session_key=session_key,
            )
        else:
            session_key = user.session_key

        # return session key
        serializer = LoginTest.OutputSerializer(instance={
            'session_key': session_key,
        })
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class Logout(generics.GenericAPIView):
    '''Logout API view.'''

    http_method_names = ['post']
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        '''POST for logout.'''
        logout(request=request)
        return response.Response(status=status.HTTP_201_CREATED)


class JoinAsParticipant(generics.CreateAPIView):
    '''Researcher/supervisor also joins a campaign as a participant.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for JoinAsParticipant view.'''

        email = serializers.EmailField(required=True, allow_blank=False)
        campaign_id = serializers.IntegerField(required=True, allow_null=False)

        def validate(self, attrs):
            '''Validate input data.'''

            # check if user exists
            user = slc.find_user(user_id=None, email=attrs['email'])
            if not user:
                raise ValidationError('User does not exist')

            # check if campaign exists
            campaign = slc.get_campaign(campaign_id=attrs['campaign_id'])
            if not campaign:
                raise ValidationError('Campaign does not exist')
            if not slc.is_supervisor(campaign=campaign, user=user):
                raise ValidationError(
                    'User is not a supervisor'
                )  # should be available to researchers only

            # check if user is already a participant
            participant = slc.get_participant(campaign=campaign, user=user)
            if participant:
                raise ValidationError('User is already a participant')

            return attrs

    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        '''CREATE method for JoinAsParticipant.'''

        # validate input data
        serializer = JoinAsParticipant.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create participant with email and campaign_id
        email = serializer.validated_data['email']
        campaign_id = serializer.validated_data['campaign_id']
        svc.add_campaign_participant(
            campaign=slc.get_campaign(campaign_id=campaign_id),
            add_user=slc.find_user(user_id=None, email=email),
        )
        return response.Response(status=status.HTTP_201_CREATED)


class CreateCampaign(generics.CreateAPIView):
    '''Create a new campaign.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for JoinAsParticipant view.'''

        class DataSourceSerializer(serializers.Serializer):
            '''Data source serializer for CreateCampaign view.'''

            class ColumnSerializer(serializers.Serializer):
                '''Column serializer for CreateCampaign view.'''

                name = serializers.CharField(required=True, allow_blank=False)
                column_type = serializers.CharField(required=True,
                                                    allow_blank=False)
                is_categorical = serializers.BooleanField(required=True,
                                                          allow_null=False)
                accept_values = serializers.CharField(required=False,
                                                      allow_null=True)

                def validate(self, attrs):
                    '''Validate input data.'''
                    validated = super().validate(attrs)

                    # check if column type is valid
                    valid_types = ['timestamp', 'text', 'integer', 'float']
                    if validated['column_type'].lower() not in valid_types:
                        raise ValidationError(
                            f'Column type must be one of {valid_types}')

                    # text must be categorical
                    is_text_type = validated['column_type'].lower() == 'text'
                    if is_text_type and not validated['is_categorical']:
                        raise ValidationError(
                            'Text columns must be categorical')
                    validated['column_type'] = validated['column_type'].lower()

                    # acceptable values must be provided only for categorical columns
                    is_categorical = validated['is_categorical']
                    has_accept_values = validated.get('accept_values', None)
                    if has_accept_values and not is_categorical:
                        raise ValidationError(
                            'Acceptable values can only be provided for categorical columns'
                        )

                    return validated

            name = serializers.CharField(required=True, allow_blank=False)
            columns = serializers.ListField(
                child=ColumnSerializer(),
                allow_empty=True,
                required=False,
                allow_null=True,
            )

            def validate(self, attrs):
                '''Validate input data.'''
                validated = super().validate(attrs)

                # get data source
                data_source = slc.find_data_source(
                    data_source_id=None,
                    name=validated['name'],
                )

                # if no columns are provided, then the data source must already exist
                no_columns = validated.get('columns', []) == []
                no_data_source = data_source is None
                if no_columns and no_data_source:
                    raise ValidationError(
                        'Data source with provided name does not exist and no columns are provided'
                    )

                return validated

        email = serializers.EmailField(
            required=True,
            allow_blank=False,
            allow_null=False,
        )
        name = serializers.CharField(required=True, allow_blank=False)
        description = serializers.CharField(required=True, allow_blank=True)
        start_datetime = serializers.DateTimeField(required=True)
        end_datetime = serializers.DateTimeField(required=True)
        data_sources = serializers.JSONField(required=True)

        def validate(self, attrs):
            '''Validate input data.'''
            validated = super().validate(attrs)

            # check data_sources json
            data_source_srz = CreateCampaign.InputSerializer.DataSourceSerializer(
                data=validated['data_sources'],
                many=True,
            )
            if not data_source_srz.is_valid():
                raise ValidationError(data_source_srz.errors)
            validated['data_sources'] = data_source_srz.validated_data

            # check if user exists
            user = slc.find_user(user_id=None, email=validated['email'])
            if not user:
                raise ValidationError(
                    f'User {validated["email"]} does not exist')

            # remove timezone info from datetimes
            validated['start_datetime'] = validated['start_datetime'].replace(
                tzinfo=None)
            validated['end_datetime'] = validated['end_datetime'].replace(
                tzinfo=None)

            return validated

    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        '''CREATE method for CreateCampaign view.'''

        # validate input data
        serializer = CreateCampaign.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # get campaign owner user
        owner = slc.find_user(
            user_id=None,
            email=serializer.validated_data['email'],
        )

        # create (or select existing) data sources
        data_sources = []
        for data_source in serializer.validated_data['data_sources']:

            # selected or created data_source stored in tmp
            if data_source.get('columns', None) is None:
                # existing data source
                tmp = slc.find_data_source(
                    data_source_id=None,
                    name=data_source['name'],
                )
            else:
                # new data source
                # create columns
                columns: List[mdl.Column] = []
                for column in data_source['columns']:
                    columns.append(
                        svc.create_column(
                            name=column['name'],
                            column_type=column['column_type'],
                            is_categorical=column['is_categorical'],
                            accept_values=column.get('accept_values', None),
                        ))
                # create data source
                tmp = svc.create_data_source(
                    name=data_source['name'],
                    columns=columns,
                )

            # add to data sources list
            data_sources.append(tmp)

        # create campaign (and attach it to owner_user)
        svc.create_campaign(
            owner=owner,
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description'],
            start_ts=serializer.validated_data['start_datetime'],
            end_ts=serializer.validated_data['end_datetime'],
            data_sources=data_sources,
        )

        return response.Response(status=status.HTTP_201_CREATED)


class EditCampaign(generics.UpdateAPIView):
    '''Researcher/supervisor also joins a campaign as a participant.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for JoinAsParticipant view.'''

        class DataSourceSerializer(serializers.Serializer):
            '''Data source serializer for CreateCampaign view.'''

            class ColumnSerializer(serializers.Serializer):
                '''Column serializer for CreateCampaign view.'''

                name = serializers.CharField(required=True, allow_blank=False)
                column_type = serializers.CharField(required=True,
                                                    allow_blank=False)
                is_categorical = serializers.BooleanField(required=True,
                                                          allow_null=False)
                accept_values = serializers.CharField(required=False,
                                                      allow_null=True)

                def validate(self, attrs):
                    '''Validate input data.'''
                    validated = super().validate(attrs)

                    # check if column type is valid
                    valid_types = ['timestamp', 'text', 'integer', 'float']
                    if validated['column_type'].lower() not in valid_types:
                        raise ValidationError(
                            f'Column type must be one of {valid_types}')

                    # text must be categorical
                    is_text_type = validated['column_type'].lower() == 'text'
                    if is_text_type and not validated['is_categorical']:
                        raise ValidationError(
                            'Text columns must be categorical')
                    validated['column_type'] = validated['column_type'].lower()

                    # acceptable values must be provided only for categorical columns
                    is_categorical = validated['is_categorical']
                    has_accept_values = validated.get('accept_values', None)
                    if has_accept_values and not is_categorical:
                        raise ValidationError(
                            'Acceptable values can only be provided for categorical columns'
                        )

                    return validated

            name = serializers.CharField(required=True, allow_blank=False)
            columns = serializers.ListField(
                child=ColumnSerializer(),
                required=False,
                allow_empty=True,
            )

            def validate(self, attrs):
                '''Validate input data.'''
                validated = super().validate(attrs)

                # get data source
                data_source = slc.find_data_source(
                    data_source_id=None,
                    name=validated['name'],
                )

                # if no columns are provided, then the data source must already exist
                no_columns = validated.get('columns', []) == []
                no_data_source = data_source is None
                if no_columns and no_data_source:
                    raise ValidationError(
                        'Data source with provided name does not exist and no columns are provided'
                    )

                return validated

        email = serializers.EmailField(
            required=True,
            allow_blank=False,
            allow_null=False,
        )
        campaign_id = serializers.IntegerField(required=True)
        name = serializers.CharField(required=True, allow_blank=False)
        description = serializers.CharField(required=True, allow_blank=True)
        start_datetime = serializers.DateTimeField(required=True)
        end_datetime = serializers.DateTimeField(required=True)
        data_sources = serializers.JSONField(required=True)

        def validate(self, attrs):
            '''Validate input data.'''
            validated = super().validate(attrs)

            # check data_sources json
            data_source_srz = EditCampaign.InputSerializer.DataSourceSerializer(
                data=validated['data_sources'],
                many=True,
            )
            if not data_source_srz.is_valid():
                raise ValidationError(data_source_srz.errors)
            validated['data_sources'] = data_source_srz.validated_data

            # check if user exists
            user = slc.find_user(user_id=None, email=validated['email'])
            if not user:
                raise ValidationError(
                    f'User {validated["email"]} does not exist')

            # validate campaign
            campaign = slc.get_campaign(campaign_id=validated['campaign_id'])
            if not campaign:
                raise ValidationError(
                    f'Campaign {validated["campaign_id"]} does not exist')

            # check user is researcher/supervisor
            if not slc.is_supervisor(campaign=campaign, user=user):
                raise ValidationError(
                    f'User {validated["email"]} is not a researcher/supervisor for campaign {campaign.name}'
                )

            # remove timezone info from datetimes
            validated['start_datetime'] = validated['start_datetime'].replace(
                tzinfo=None)
            validated['end_datetime'] = validated['end_datetime'].replace(
                tzinfo=None)

            return validated

    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        '''UPDATE method for JoinAsParticipant view.'''

        # validate input data
        serializer = EditCampaign.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # update campaign metadata
        campaign_id = serializer.validated_data['campaign_id']
        campaign = slc.get_campaign(campaign_id=campaign_id)
        campaign.name = serializer.validated_data['name']
        campaign.description = serializer.validated_data['description']
        campaign.start_datetime = serializer.validated_data['start_datetime']
        campaign.end_datetime = serializer.validated_data['end_datetime']
        campaign.save()

        # remove previous campaign data sources
        for data_source in slc.get_campaign_data_sources(campaign=campaign):
            svc.remove_campaign_data_source(
                campaign=campaign,
                data_source=data_source,
            )

        # add new data sources
        for data_source in serializer.validated_data['data_sources']:

            # selected or created data_source stored in tmp
            if data_source.get('columns', None) is None:
                # existing data source
                tmp = slc.find_data_source(
                    data_source_id=None,
                    name=data_source['name'],
                )
            else:
                # new data source
                columns: List[mdl.Column] = []
                for column in data_source['columns']:
                    columns.append(
                        svc.create_column(
                            name=column['name'],
                            column_type=column['column_type'],
                            is_categorical=column['is_categorical'],
                            accept_values=column.get('accept_values', None),
                        ))

                # create data source
                tmp = svc.create_data_source(
                    name=data_source['name'],
                    columns=columns,
                )

            # add to data sources list
            svc.add_campaign_data_source(campaign=campaign, data_source=tmp)

        return response.Response(status=status.HTTP_201_CREATED)


class DeleteCampaign(generics.DestroyAPIView):
    '''Delete campaign view.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for DeleteCampaign view.'''

        email = serializers.EmailField(required=True, allow_blank=False)
        campaign_id = serializers.IntegerField(required=True, allow_null=False)

        def validate(self, attrs):
            '''Validate input data.'''

            # check if user exists
            user = slc.find_user(user_id=None, email=attrs['email'])
            if not user:
                raise ValidationError('User does not exist')

            # check if campaign exists
            campaign = slc.get_campaign(campaign_id=attrs['campaign_id'])
            if not campaign:
                raise ValidationError('Campaign does not exist')
            if campaign.owner != user:
                raise ValidationError('User is not the owner of the campaign')

            return attrs

    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        '''DELETE method for DeleteCampaign view.'''

        # validate input data
        serializer = DeleteCampaign.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # delete campaign
        campaign_id = serializer.validated_data['campaign_id']
        campaign = slc.get_campaign(campaign_id=campaign_id)
        campaign.delete().execute()

        return response.Response(status=status.HTTP_200_OK)


class UploadCSV(generics.CreateAPIView):

    class InputSerializer(serializers.Serializer):
        '''Input serializer for UploadCSV view.'''

        email = serializers.EmailField(
            required=True,
            allow_blank=False,
        )
        campaign_id = serializers.IntegerField(
            required=True,
            allow_null=False,
        )
        data_source_id = serializers.IntegerField(
            required=True,
            allow_null=False,
        )
        files = serializers.ListField(child=serializers.FileField(
            allow_empty_file=False,
            use_url=False,
        ))

        def validate(self, attrs):
            '''Validate input data.'''

            # check if user exists
            user = slc.find_user(user_id=None, email=attrs['email'])
            if not user:
                raise ValidationError('User does not exist')

            # check if campaign exists
            campaign = slc.get_campaign(campaign_id=attrs['campaign_id'])
            if not campaign:
                raise ValidationError('Campaign does not exist')
            if not slc.is_supervisor(campaign=campaign, user=user):
                raise ValidationError(
                    'User is not a supervisor'
                )  # should be available to researchers only

            # check if data source exists
            data_source = slc.find_data_source(
                data_source_id=attrs['data_source_id'],
                name=None,
            )
            if not data_source:
                raise ValidationError('Data source does not exist')

            # get columns for comparing with CSV file
            columns = slc.get_data_source_columns(data_source=data_source)
            columns_py_types = {
                'timestamp': datetime,
                'text': str,
                'integer': int,
                'float': float,
            }
            dtypes = dict()
            for column in columns:
                dtypes[column.name] = columns_py_types[column.column_type]

            # check files
            for file in attrs['files']:
                # check if file is a CSV file
                if file.content_type != 'text/csv':
                    raise ValidationError('File is not a CSV file')

                # check columns using pandas
                try:
                    df = pd.read_csv(file, dtype=dtypes)
                except Exception as e:
                    raise ValidationError(e) from e

                # participant id column is required
                if 'participant_id' not in df.columns:
                    raise ValidationError(
                        f'Participant id column is missing in {file.name}')

            return attrs

    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        '''POST method for JoinAsParticipant view.'''

        # validate input data
        serializer = UploadCSV.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create participant with email and campaign_id
        email = serializer.validated_data['email']
        campaign_id = serializer.validated_data['campaign_id']
        svc.add_campaign_participant(
            campaign=slc.get_campaign(campaign_id=campaign_id),
            add_user=slc.find_user(user_id=None, email=email),
        )
        return response.Response(status=status.HTTP_201_CREATED)
