from django import template

register = template.Library()


@register.filter
def fix_localhost(value: str):
	return value.replace('host.docker.internal', 'localhost').replace('172.17.0.1', 'localhost')
