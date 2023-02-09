'''This file is used to configure the api app'''

from django.apps import AppConfig


class ApiConfig(AppConfig):
    '''This class is used to configure the api app'''
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        import api.signals  # pylint: disable=unused-import, import-outside-toplevel
