from os import getenv

from easytrack.utils import notnull


def export_vars(_):
    '''Export variables to the template context.'''
    return dict(
        STATIC_HOST=notnull(getenv(key='STATIC_HOST')),
        STATIC_PORT=notnull(getenv(key='STATIC_PORT')),
        GOOGLE_API_KEY=notnull(getenv(key='GOOGLE_API_KEY')),
        GOOGLE_CLIENT_ID=notnull(getenv(key='GOOGLE_CLIENT_ID')),
    )
