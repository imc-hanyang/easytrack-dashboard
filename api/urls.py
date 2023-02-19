''' API URLS '''

from django.urls import path
from api import views

urlpatterns = [
    # google oauth login
    path(
        'login-google',
        views.LoginGoogle.as_view(),
        name='google-login-api',
    ),

    # test account
    path(
        'login-demo',
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
        'join-as-participant/',
        views.JoinAsParticipant.as_view(),
        name='join-as-participant-api',
    ),

    # create campaign
    path(
        'create-campaign/',
        views.CreateCampaign.as_view(),
        name='create-campaign-api',
    ),

    # update existing campaign
    path(
        'edit-campaign/',
        views.EditCampaign.as_view(),
        name='edit-campaign-api',
    ),

    # delete campaign
    path(
        'delete-campaign/',
        views.DeleteCampaign.as_view(),
        name='delete-campaign-api',
    ),

    # upload csv file
    path(
        'upload-csv/',
        views.UploadCSV.as_view(),
        name='upload-csv-api',
    ),
]
