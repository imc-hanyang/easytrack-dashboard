'''Template tags for the dashboard app.'''

# stdlib
from datetime import datetime

# 3rd party
from django import template
from easytrack import utils

register = template.Library()


@register.filter
def timestamp_hreadable(timestamp: datetime):
    '''Return a human readable timestamp.'''

    if timestamp.year == datetime.fromtimestamp(0).year:
        return 'n/a'
    return utils.datetime_to_str(timestamp=timestamp, js_format=False)
