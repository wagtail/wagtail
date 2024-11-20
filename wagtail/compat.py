from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")
# Two additional settings that are useful in South migrations when
# specifying the user model in the FakeORM
try:
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit(".", 1)
except ValueError:
    raise ImproperlyConfigured(
        "AUTH_USER_MODEL must be of the form" " 'app_label.model_name'"
    )


try:
    from http import HTTPMethod
except ImportError:
    # For Python < 3.11
    from enum import Enum

    class HTTPMethod(Enum):
        GET = "GET"
        HEAD = "HEAD"
        OPTIONS = "OPTIONS"
        POST = "POST"
        PUT = "PUT"
        DELETE = "DELETE"
        PATCH = "PATCH"
