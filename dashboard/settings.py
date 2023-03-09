''' Django settings for dashboard project. '''

# stdlib
from os import getenv
from os.path import join
from os.path import dirname
from os.path import abspath
import socket

# 3rd party
from dotenv import load_dotenv
from easytrack.utils import notnull
from easytrack import init

# Load environment variables from .env file (if exists)
load_dotenv()

# Database credentials
POSTGRES_HOST = notnull(getenv(key='POSTGRES_HOST'))
POSTGRES_PORT = int(notnull(getenv(key='POSTGRES_PORT')))
POSTGRES_DBNAME = notnull(getenv(key='POSTGRES_DBNAME'))
POSTGRES_USER = notnull(getenv(key='POSTGRES_USER'))
POSTGRES_PASSWORD = notnull(getenv(key='POSTGRES_PASSWORD'))

# Initialize easytrack module (core)
init(
    db_host=POSTGRES_HOST,
    db_port=POSTGRES_PORT,
    db_name=POSTGRES_DBNAME,
    db_user=POSTGRES_USER,
    db_password=POSTGRES_PASSWORD,
)

# Django app deoployment settings
ALLOWED_HOSTS = []
INTERNAL_IPS = []

# Deployment mode (debug or production)
DEBUG = getenv(key='DEBUG', default='False').lower() == 'true'

if DEBUG:
    # Deployed in debug mode

    # Allow all host headers during development
    ALLOWED_HOSTS.append('*')

    # Show debug toolbar only for internal IPs
    internal_ips = getenv(key='INTERNAL_IPS', default='')
    if internal_ips:
        internal_ips = internal_ips.replace(' ', '').split(',')
        INTERNAL_IPS.extend(internal_ips)

    # Docker host IP (for debug toolbar when using docker)
    _, _, ips = socket.gethostbyname_ex(socket.gethostname())
    for ip in ips:
        INTERNAL_IPS.append('.'.join(ip.split('.')[:-1] + ['1']))
else:
    # Deployed in production mode

    # Allow only specific host headers during production
    allowed_hosts = getenv(key='ALLOWED_HOSTS', default='')
    if allowed_hosts:
        allowed_hosts = allowed_hosts.replace(' ', '').split(',')
        ALLOWED_HOSTS.extend(allowed_hosts)
    else:
        raise ValueError('ALLOWED_HOSTS is not set in environment variables')

# Django project root directory inferred from current file
BASE_DIR = dirname(dirname(abspath(__file__)))

# Django apps (e.g. admin, and custom apps)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'social_django',
    'dashboard',
    'api',
]

# Django middleware (e.g. authentication, sessions)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Django template settings (e.g. directories, context processors)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join(BASE_DIR, 'templates')],
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

# Django database settings (e.g. engine, host, user)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
        'NAME': POSTGRES_DBNAME,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD,
    }
}

# Django static files
STATICFILES_DIRS = [
    join(BASE_DIR, "dashboard", "static"),
]
STATIC_URL = 'static/'
STATIC_ROOT = 'static/'

# Django internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Google OAuth2 settings
AUTHENTICATION_BACKENDS = (
    # 'social_core.backends.google.GoogleOpenId',
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google_openidconnect.GoogleOpenIdConnect',
    'social_core.backends.google.GoogleOAuth2',
)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = notnull(
    getenv(key='SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'))
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = notnull(
    getenv(key='SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'))

# Django authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'login'
LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL

# Django session settings
SITE_ID = 1
SECRET_KEY = notnull(getenv('DJANGO_SECRET_KEY'))
ROOT_URLCONF = 'dashboard.urls'
WSGI_APPLICATION = 'dashboard.wsgi.application'
