'''Check if user is a participant of a campaign'''
from django import template
from easytrack import selectors as slc
from easytrack import models as mdl

register = template.Library()


@register.filter
def is_user_participant(user: mdl.User, campaign: mdl.Campaign):
    '''Check if user is a participant of a campaign'''
    return slc.is_participant(campaign=campaign, user=user)
