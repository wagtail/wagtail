import locale

from pytz import country_timezones
import six

from .maps import tz_cities


def get_country_timezones(country_code):
    """
    Retrieves the timezones for a given country, sorted in alphabetical order
    """

    tz_list = []

    if country_code in country_timezones:
        tzs = country_timezones[country_code]
        tz_list = [(t, tz_cities[t]) for t in tzs]
        tz_list.sort(lambda x, y: locale.strcoll(x[1], y[1]))

    return tz_list


def get_country_code_from_tz(tz):
    """
    Retrieves the country matching a given timezone
    """

    for c, t in six.iteritems(country_timezones):
        if tz in t:
            return c
    return None
