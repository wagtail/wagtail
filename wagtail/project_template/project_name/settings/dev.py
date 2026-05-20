from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "{{ secret_key }}"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

{% spaceless %}
{# Remove the if block when Django 6.0 support is dropped #}
{% if django_version|slice:":3" <= "6.0" %}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
{% else %}
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
{% endif %}
{% endspaceless %}

try:
    from .local import *
except ImportError:
    pass
