'''API module views.'''

# stdlib
from os.path import join

# django
from rest_framework import generics, permissions, authentication
from rest_framework import serializers
from rest_framework import response, status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

# local
from api import models as mdl
from api import serializers as srz
from dashboard import settings


class SignUp(generics.CreateAPIView):
    serializer_class = srz.SignUpInputSerializer
    queryset = mdl.User.objects.all()

    def perform_create(self, serializer: srz.SignUpInputSerializer):
        user: mdl.User = serializer.save()
        user.set_password(user.password)
        user.save()


class SignIn(generics.GenericAPIView):
    '''Sign in view.''' ''

    serializer_class = srz.SignInInputSerializer

    def post(self, request):
        '''Sign in user.'''

        serializer = srz.SignInInputSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return response.Response(
                dict(credentials='Incorrect credentials'),
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = Token.objects.get(user=user)
        serializer = srz.ReadOnlyTokenModelSerializer(instance=token)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class SubmitData(generics.CreateAPIView):
    '''Submit data view.'''

    class InputSerializer(serializers.Serializer):
        '''Input serializer for submit data view.''' ''

        file = serializers.FileField(required=True, allow_empty_file=False)

        class Meta:
            '''Meta class for InputSerializer.'''
            fields = '__all__'

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InputSerializer

    def post(self, request, *args, **kwargs):
        '''Submit data.'''

        serializer = SubmitData.InputSerializer(data=request.data)

        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # prepare user's directory
        filepath = join(settings.DATA_DUMP_DIR, f'{request.user.email}.csv')

        # save the files
        file = serializer.validated_data['file']
        with open(join(filepath), 'ab+') as wb:
            wb.write(file.read())

        return response.Response(status=status.HTTP_200_OK)
