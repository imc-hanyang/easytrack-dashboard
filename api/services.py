'''Services module for making changes to the database.'''

# local
from api import models as mdl


def create_user(
    username: str,
    email: str,
    full_name: str,
    gender: str,
    date_of_birth: str,
    password: str,
) -> mdl.User:
    '''Create a new user in the database.'''

    return mdl.User.objects.create_user(
        username=username,
        email=email,
        full_name=full_name,
        gender=gender,
        date_of_birth=date_of_birth,
        password=password,
    )
