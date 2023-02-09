'''API module routing.'''

# django
from django.urls import path

# local
from api import views

urlpatterns = [
    # authentification views
    path(
        'sign_up',
        views.SignUp.as_view(),
        name='signUpApi',
    ),
    path(
        'sign_in',
        views.SignIn.as_view(),
        name='signInApi',
    ),

    # file submission views
    path(
        'submit_data',
        views.SubmitData.as_view(),
        name='submitDataApi',
    ),
]
