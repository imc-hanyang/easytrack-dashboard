from django import template

register = template.Library()


@register.filter
def fix_localhost(value: str):
	return value.replace('host.docker.internal', 'localhost')
