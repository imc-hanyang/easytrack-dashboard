''' API URLS '''

from django.urls import path
from api import views

urlpatterns = [
    # google oauth login
    path(
        'login_google',
        views.LoginGoogle.as_view(),
        name='google-login-api',
    ),

    # test account
    path(
        'login_demo',
        views.LoginTest.as_view(),
        name='demo-login-api',
    ),

    # logout
    path(
        'logout',
        views.Logout.as_view(),
        name='logout-api',
    ),

    # join campaign (participant)
    path(
        'join_as_participant/',
        views.JoinAsParticipant.as_view(),
        name='join-as-participant-api',
    ),

    # create campaign
    path(
        'create_campaign/',
        views.CreateCampaign.as_view(),
        name='create-campaign-api',
    ),

    # update existing campaign
    path(
        'edit_campaign/',
        views.EditCampaign.as_view(),
        name='edit-campaign-api',
    ),
]
