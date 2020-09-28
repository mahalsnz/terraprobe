from ._base import *

DEBUG = False

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
CORS_ORIGIN_ALLOW_ALL = True

LOGLEVEL = os.environ.get('LOGLEVEL', 'debug').upper()
