''' Dashboard URLS '''

# 3rd party
from django.urls import path, include

# local
from dashboard import views

urlpatterns = [
    # google oAuth and site veriification
    path('google-auth/', include('social_django.urls', namespace='social')),
    path('google-site-verification.html', views.handle_google_verification),

    # REST APIs
    path(
        'api/',
        include('api.urls'),
    ),

    # Login page
    path(
        'login/',
        views.login,
        name='login',
    ),

    # Campaigns (Index)
    path(
        '',
        views.campaigns,
        name='campaigns',
    ),

    # Participants (Campaign -> Participants)
    path(
        'participants/',
        views.participants,
        name='participants',
    ),

    # Data sources and statistics (Campaign -> Participant -> Data sources and statistics)
    path(
        'data_sources/',
        views.data_sources,
        name='data-sources',
    ),

    # Raw data records (Campaign -> Participant -> Data source -> Raw data records)
    path(
        'data_records/',
        views.data_records,
        name='data-records',
    ),

    # Campaign editor (Campaign -> Edit)
    path(
        'edit/',
        views.campaign_editor,
        name='campaign-editor',
    ),

    # Dataset information (participants and data sources)
    path(
        'dataset-info/',
        views.dataset_info,
        name='dataset-info',
    ),

    # Researcher management
    path(
        'researchers/',
        views.manage_researchers,
        name='manage-researchers',
    ),

    # Data quality monitoring
    path(
        'dq-monitor/',
        views.dq_monitor,
        name='dq-monitor',
    ),
]
