'''Serializers for API models.'''
# pylint: disable=too-few-public-methods

# django
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from django.utils.timezone import datetime

# local
from api import models as mdl
from api import selectors as slc
from api import services as svc


# models serializers
class UserModelSerializer(serializers.ModelSerializer):
    '''Serializer for User model.'''
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(
        max_length=64,
        allow_blank=False,
        allow_null=False,
        required=True,
    )
    gender = serializers.CharField(
        max_length=1,
        allow_blank=False,
        allow_null=False,
        required=True,
    )
    date_of_birth = serializers.DateField(
        allow_null=False,
        required=True,
    )
    fcm_token = serializers.CharField(
        max_length=256,
        allow_blank=False,
        allow_null=False,
        required=True,
    )

    class Meta:
        '''Meta class for UserSerializer.'''
        model = mdl.User
        fields = '__all__'


class ReadOnlyTokenModelSerializer(serializers.ModelSerializer):
    '''Serializer for Token model.'''
    token = serializers.CharField(read_only=True, source='key')

    class Meta:
        '''Meta class for ReadOnlyTokenSerializer.'''
        model = Token
        fields = ['token']


# input serializers
class SignUpInputSerializer(serializers.Serializer):
    '''Input serializer for sign up view.'''

    email = serializers.EmailField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    full_name = serializers.CharField(
        max_length=128,
        required=True,
        allow_blank=False,
        allow_null=False,
    )
    gender = serializers.CharField(
        max_length=1,
        required=True,
        allow_blank=False,
        allow_null=False,
    )
    date_of_birth = serializers.DateField(
        input_formats=[r'%Y%m%d'],
        required=True,
        allow_null=False,
    )
    fcm_token = serializers.CharField(
        max_length=256,
        default=None,
        allow_blank=True,
        allow_null=True,
    )
    password = serializers.CharField(
        required=True,
        allow_null=False,
        min_length=8,
    )

    def validate(self, attrs):
        '''Validate input data.'''

        if slc.get_user(email=attrs['email']):
            raise ValidationError('Email already registered')

        if attrs['gender'] not in ['f', 'F', 'm', 'M']:
            raise ValidationError('Gender can be "F" or "M" only')
        attrs['gender'] = attrs['gender'].upper()

        if attrs['date_of_birth'] > datetime.today().date():
            raise ValidationError('Date of birth cannot be in future!')

        return attrs

    def create(self, validated_data):
        return svc.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            gender=validated_data['gender'],
            date_of_birth=validated_data['date_of_birth'],
            password=validated_data['password'],
        )

    def update(self, instance, validated_data):
        return svc.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            gender=validated_data['gender'],
            date_of_birth=validated_data['date_of_birth'],
            password=validated_data['password'],
        )

    class Meta:
        '''Meta class for InputSerializer.'''

        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


class SignInInputSerializer(serializers.Serializer):
    '''Input serializer for sign in view.'''

    email = serializers.EmailField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    password = serializers.CharField(
        required=True,
        allow_null=False,
        min_length=8,
    )

    def create(self, validated_data):
        return super().create(validated_data)

    class Meta:
        '''Meta class for InputSerializer.'''

        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}
