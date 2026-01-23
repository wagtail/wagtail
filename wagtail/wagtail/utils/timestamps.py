import datetime

from django.conf import settings
from django.utils import formats, timezone
from django.utils.dateparse import parse_datetime


def ensure_utc(value):
    """
    Similar to how django-modelcluster stores the revision's data and similar to how
    django stores dates in the database, this converts the date to UTC if required.
    """
    # https://github.com/wagtail/django-modelcluster/blob/8666f16eaf23ca98afc160b0a4729864411c0563/modelcluster/models.py#L21-L28
    if settings.USE_TZ:
        if timezone.is_naive(value):
            default_timezone = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_timezone).astimezone(
                datetime.timezone.utc
            )
        else:
            # convert to UTC
            value = timezone.localtime(value, datetime.timezone.utc)
    return value


def parse_datetime_localized(date_string):
    """
    Uses Django's parse_datetime(), but ensures to return an aware datetime.
    """
    dt = parse_datetime(date_string)
    if settings.USE_TZ and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=timezone.get_default_timezone())
    return dt


def render_timestamp(timestamp):
    """
    Helper function to format a possibly-timezone-aware datetime into the format
    used by Django (e.g. in templates).
    """
    if timezone.is_aware(timestamp):
        timestamp = timezone.localtime(timestamp)
    return formats.date_format(timestamp, "DATETIME_FORMAT")
