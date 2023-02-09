'''Context processors for the dashboard app.'''

# stdlib
from os import getenv

# local
from easytrack.utils import notnull


def export_vars(_):
    '''Export environment variables to the template context.'''
    return {
        "STATIC_HOST": notnull(getenv(key='STATIC_HOST')),
        "STATIC_PORT": notnull(getenv(key='STATIC_PORT')),
    }
