from ._base import *

PROPERTIES_API_URL = 'https://api.properties.metwatch.nz/'

DEBUG = False

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
CORS_ORIGIN_ALLOW_ALL = True

LOGLEVEL = os.environ.get('LOGLEVEL', 'debug').upper()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SOIL_DB_NAME,
        'USER': SOIL_DB_USER,
        'PASSWORD': SOIL_DB_PASSWORD,
        'HOST': 'prod-terraprobe.cqa7v3kttxp3.ap-southeast-2.rds.amazonaws.com',
        'PORT': '',
    }
}
