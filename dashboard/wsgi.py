''' WSGI config for dashboard project. '''

# stdlib
import os

# 3rd party
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
application = get_wsgi_application()
