'''Fix localhost in docker-compose'''
from django import template

register = template.Library()


@register.filter
def fix_localhost(value: str):
    '''Fix localhost in docker-compose'''
    fixes = [
        ('host.docker.internal', 'localhost'),
        ('172.17.0.1', 'localhost'),
    ]
    ans = value
    for old, new in fixes:
        ans = ans.replace(old, new)
    return ans
