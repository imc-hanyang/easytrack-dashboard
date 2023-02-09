from typing import Optional, List
from api import models as mdl
from datetime import datetime as dt
from dateutil import tz


def user_exists(id: int = None, email: str = None) -> bool:
    '''Check if user exists by id or email.'''

    # check if user exists by id
    if id:
        if not str(id).isdigit(): return False
        return mdl.User.objects.filter(id=int(id)).exists()

    # check if user exists by email
    if email:
        return mdl.User.objects.filter(email=str(email)).exists()

    return False


def get_user(id: int = None, email: str = None) -> Optional[mdl.User]:
    '''Get user by id or email.'''

    # find user by id
    if id and str(id).isdigit():
        if mdl.User.objects.filter(id=int(id)).exists():
            return mdl.User.objects.get(id=int(id))

    # find user by email
    if email and mdl.User.objects.filter(email=str(email)).exists():
        return mdl.User.objects.get(email=str(email))


def get_users(exclude_superusers=True) -> List[mdl.User]:
    '''Get all users.'''

    if exclude_superusers:
        return mdl.User.objects.filter(is_superuser=False)

    return mdl.User.objects.all()
