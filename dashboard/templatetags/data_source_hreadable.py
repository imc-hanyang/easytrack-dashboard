# stdlib
from typing import List

# django
from django import template
from easytrack import models as mdl

register = template.Library()


@register.filter
def data_source_hreadable(configurations):
  '''Return a human readable data source details such as column names.'''
  return ', '.join([item['name'] for item in sorted(configurations, key = lambda item: item['index'])])
