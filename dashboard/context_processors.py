from easytrack.utils import notnull
from os import getenv


def export_vars(_):
  return dict(
    STATIC_HOST = notnull(getenv(key = 'STATIC_HOST')),
    STATIC_PORT = notnull(getenv(key = 'STATIC_PORT')),
  )
