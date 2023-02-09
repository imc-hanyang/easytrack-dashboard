'''Signals for database changes'''
# pylint: disable=unused-argument, no-member

# django
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

# local
from api import models


@receiver(post_save, sender=models.User)
def create_auth_token(_, instance=None, created=False, **kwargs):
    '''Create an auth token when a new user is created'''
    if created:
        Token.objects.create(user=instance)
