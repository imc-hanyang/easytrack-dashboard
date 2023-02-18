'''Return a human readable data source details such as column names.'''
from django import template

register = template.Library()


@register.filter
def data_source_cols_hreadable(configurations):
    '''Return a human readable data source details such as column names.'''

    columns = []
    for item in sorted(configurations, key=lambda item: item['index']):
        columns.append(item['name'])
    return ', '.join(columns)
