'''Template tags for campaign participants count'''
from django import template
from easytrack import selectors as slc
from easytrack import models as mdl

register = template.Library()


@register.filter
def campaign_participants_count(campaign: mdl.Campaign):
    '''Template tags for campaign participants count'''
    return slc.get_campaign_participants_count(campaign=campaign)
