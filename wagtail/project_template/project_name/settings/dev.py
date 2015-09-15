from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
DEBUG_TEMPLATE = True

for i in range(0, len(TEMPLATES) - 1):
    TEMPLATES[i]['OPTIONS']['debug'] = DEBUG_TEMPLATE

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ secret_key }}'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    from .local import *
except ImportError:
    pass
