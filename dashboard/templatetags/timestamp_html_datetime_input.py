'''Template tags for the dashboard app.'''
from django import template
from easytrack import utils
from datetime import datetime

register = template.Library()


@register.filter
def timestamp_html_datetime_input(timestamp):
  '''Return a human readable timestamp.'''

  if timestamp.year == datetime.fromtimestamp(0).year:
    return 'n/a'
  tmp = utils.datetime_to_str(timestamp = timestamp, js_format = True)
  return tmp[:tmp.rindex(':')]
