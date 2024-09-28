# Patch Django's number formatting functions during tests so that outputting a number onto a
# template without explicitly passing it through one of |intcomma, |localize, |unlocalize or
# |filesizeformat will raise an exception. This helps to catch bugs where
# USE_THOUSAND_SEPARATOR = True incorrectly reformats numbers that are not intended to be
# human-readable (such as image dimensions, or IDs within data attributes).

from decimal import Decimal

import django.contrib.humanize.templatetags.humanize
import django.template.defaultfilters
import django.templatetags.l10n
import django.utils.numberformat
from django.core.exceptions import ImproperlyConfigured
from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import gettext, ngettext

original_numberformat = django.utils.numberformat.format
original_intcomma = django.contrib.humanize.templatetags.humanize.intcomma


def patched_numberformat(*args, use_l10n=None, **kwargs):
    if use_l10n is False or use_l10n == "explicit":
        return original_numberformat(*args, use_l10n=use_l10n, **kwargs)

    raise ImproperlyConfigured(
        "A number was used directly on a template. "
        "Numbers output on templates should be passed through one of |intcomma, |localize, "
        "|unlocalize or |filesizeformat to avoid issues with USE_THOUSAND_SEPARATOR."
    )


def patched_intcomma(value, use_l10n=True):
    if use_l10n:
        try:
            if not isinstance(value, (float, Decimal)):
                value = int(value)
        except (TypeError, ValueError):
            return original_intcomma(value, False)
        else:
            return formats.number_format(
                value, use_l10n="explicit", force_grouping=True
            )

    return original_intcomma(value, use_l10n=use_l10n)


def patched_filesizeformat(bytes_):
    """
    Format the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 bytes, etc.).
    """
    try:
        bytes_ = int(bytes_)
    except (TypeError, ValueError, UnicodeDecodeError):
        value = ngettext("%(size)d byte", "%(size)d bytes", 0) % {"size": 0}
        return avoid_wrapping(value)

    def filesize_number_format(value):
        return formats.number_format(round(value, 1), 1, use_l10n="explicit")

    KB = 1 << 10
    MB = 1 << 20
    GB = 1 << 30
    TB = 1 << 40
    PB = 1 << 50

    negative = bytes_ < 0
    if negative:
        bytes_ = -bytes_  # Allow formatting of negative numbers.

    if bytes_ < KB:
        value = ngettext("%(size)d byte", "%(size)d bytes", bytes_) % {"size": bytes_}
    elif bytes_ < MB:
        value = gettext("%s KB") % filesize_number_format(bytes_ / KB)
    elif bytes_ < GB:
        value = gettext("%s MB") % filesize_number_format(bytes_ / MB)
    elif bytes_ < TB:
        value = gettext("%s GB") % filesize_number_format(bytes_ / GB)
    elif bytes_ < PB:
        value = gettext("%s TB") % filesize_number_format(bytes_ / TB)
    else:
        value = gettext("%s PB") % filesize_number_format(bytes_ / PB)

    if negative:
        value = "-%s" % value
    return avoid_wrapping(value)


def patched_localize(value):
    return str(formats.localize(value, use_l10n="explicit"))


def patch_number_formats():
    django.utils.numberformat.format = patched_numberformat
    django.contrib.humanize.templatetags.humanize.intcomma = patched_intcomma
    django.template.defaultfilters.filesizeformat = patched_filesizeformat
    django.template.defaultfilters.register.filter(
        "filesizeformat", patched_filesizeformat, is_safe=True
    )
    django.templatetags.l10n.localize = patched_localize
    django.templatetags.l10n.register.filter(
        "localize", patched_localize, is_safe=False
    )
