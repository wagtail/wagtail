import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format


def submittable_timestamp(timestamp):
    """
    Helper function to translate a possibly-timezone-aware datetime into the format used in the
    go_live_at / expire_at form fields - "YYYY-MM-DD hh:mm", with no timezone indicator.
    This will be interpreted as being in the server's timezone (settings.TIME_ZONE), so we
    need to pass it through timezone.localtime to ensure that the client and server are in
    agreement about what the timestamp means.
    """
    if timezone.is_aware(timestamp):
        return timezone.localtime(timestamp).strftime("%Y-%m-%d %H:%M")
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M")


def rendered_timestamp(timestamp):
    """
    Helper function to format a possibly-timezone-aware datetime into the format
    used by Django (e.g. in templates).
    """
    if timezone.is_aware(timestamp):
        timestamp = timezone.localtime(timestamp)
    return date_format(timestamp, settings.DATETIME_FORMAT)


def local_datetime(*args):
    dt = datetime.datetime(*args)
    return timezone.make_aware(dt)
