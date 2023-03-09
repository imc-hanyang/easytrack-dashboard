''' Context processors for the dashboard app. '''

# stdlib
from os import getenv

# 3rd party
from easytrack.utils import notnull


def export_vars(request):
    '''Export environment variables to the template context.'''

    return {
        # Google oAuth2 credentials
        'GOOGLE_API_KEY': notnull(getenv(key='GOOGLE_API_KEY')),
        'GOOGLE_CLIENT_ID': notnull(getenv(key='GOOGLE_CLIENT_ID')),
    }
