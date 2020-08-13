from ._base import *

DEBUG = True

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True

LOGLEVEL = os.environ.get('LOGLEVEL', 'info').upper()
