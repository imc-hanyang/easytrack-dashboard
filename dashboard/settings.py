'''Django settings for dashboard project.'''
# pylint: disable=line-too-long

# stdlib
from os import environ
import os
import sys

# 3rd party
from dotenv import load_dotenv
from easytrack.utils import notnull
from easytrack import init
from easytrack import models as mdl

# load .env into environment
load_dotenv()
db_host = notnull(os.getenv(key='POSTGRES_HOST'))
db_port = int(notnull(os.getenv(key='POSTGRES_PORT')))
db_name = notnull(os.getenv(key='POSTGRES_DBNAME'))
db_name_test = notnull(os.getenv(key='POSTGRES_TEST_DBNAME'))
db_user = notnull(os.getenv(key='POSTGRES_USER'))
db_password = notnull(os.getenv(key='POSTGRES_PASSWORD'))

DEV_EMAIL = 'dev@easytrack.com'
DATA_DUMP_DIR = notnull(os.getenv(key='DATA_DUMP_DIR'))

DEBUG = True
ALLOWED_HOSTS = environ['SERVERNAMES'].replace(' ', '').split(',')
INTERNAL_IPS = environ['INTERNAL_IPS'].replace(' ', '').split(',')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'social_django',
    'dashboard',
    'api',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.export_vars',
            ],
        },
    },
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': db_host,
        'PORT': db_port,
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTHENTICATION_BACKENDS = (
    # 'social_core.backends.google.GoogleOpenId',
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google_openidconnect.GoogleOpenIdConnect',
    'social_core.backends.google.GoogleOAuth2',
)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "79296265957-khvficocpqmhajv3c5obiljo2k95jqt3.apps.googleusercontent.com"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "u4SAx6SzM7vBwXYAYCW0OGLe"

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'login'
LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL

SITE_ID = 1
SECRET_KEY = 'cnbtigdbatfgl5iw89bh*$-y4j@g!c)qtuwmmi=ld!d^-he3o)'
ROOT_URLCONF = 'dashboard.urls'
WSGI_APPLICATION = 'dashboard.wsgi.application'

# init peewee ORM
init(
    db_host=db_host,
    db_port=db_port,
    db_name=db_name,
    db_user=db_user,
    db_password=db_password,
)

# user model for auth
AUTH_USER_MODEL = 'api.User'

# test database
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase'
    }
