''' Views for the API app. '''

# stdlib
from os import getenv
from time import time_ns

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
from easytrack import utils as et_utils


class LoginGoogle(generics.GenericAPIView):

    class InputSerializer(serializers.Serializer):
        id_token = serializers.CharField(
            required=True,
            allow_null=False,
            allow_blank=False,
        )

        def validate(self, attrs):
            google_id_details = id_token.verify_oauth2_token(
                id_token=attrs['id_token'],
                request=oauth_requests.Request(),
            )
            valid_iss = ['accounts.google.com', 'https://accounts.google.com']
            if google_id_details['iss'] not in valid_iss:
                raise ValidationError('Invalid id_token issuer')

            return attrs

        class Meta:
            fields = '__all__'

    class OutputSerializer(serializers.Serializer):
        session_key = serializers.CharField()

    http_method_names = ['post']
    serializer_class = InputSerializer

    def post(self, request, *args, **kwargs):
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

    class OutputSerializer(serializers.Serializer):
        session_key = serializers.CharField()

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
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
    http_method_names = ['post']
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request=request)
        return response.Response(status=status.HTTP_201_CREATED)


class JoinAsParticipant(generics.GenericAPIView):
    '''Researcher/supervisor also joins a campaign as a participant.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for JoinAsParticipant view.'''

        email = serializers.EmailField(required=True)
        campaign_id = serializers.IntegerField(required=True)

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

        class Meta:
            fields = '__all__'

    http_method_names = ['post']
    serializer_class = InputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = JoinAsParticipant.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        logout(request=request)
        return response.Response(status=status.HTTP_201_CREATED)
