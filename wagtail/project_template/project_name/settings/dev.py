from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ secret_key }}'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    from .local import *
except ImportError:
    pass
