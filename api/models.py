'''Models for the API app.'''

# django
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

# 3rd party
from easytrack import models as mdl


class User(AbstractUser):
    full_name = models.CharField(max_length=128)
    gender = models.CharField(max_length=1)
    date_of_birth = models.DateField()

    REQUIRED_FIELDS = ['full_name', 'gender', 'date_of_birth']
