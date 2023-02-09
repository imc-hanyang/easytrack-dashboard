'''Fixes the host address issue inside a docker container'''

from django import template

register = template.Library()


@register.filter
def fix_docker_localhost(value: str):
    '''Fixes the host address issue inside a docker container'''
    return value.replace(
        'host.docker.internal',
        'localhost',
    ).replace(
        '172.17.0.1',
        'localhost',
    )
