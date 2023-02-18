''' API URLS '''

from django.urls import path
from api import views

urlpatterns = [
    # google oauth login
    path(
        'login_google',
        views.LoginGoogle.as_view(),
        name='googleLoginApi',
    ),

    # test account
    path(
        'login_demo',
        views.LoginTest.as_view(),
        name='demoLoginApi',
    ),

    # logout
    path(
        'logout',
        views.Logout.as_view(),
        name='logoutApi',
    ),
]
