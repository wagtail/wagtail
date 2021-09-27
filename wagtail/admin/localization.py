import functools
import gettext
import os

import zoneinfo
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.utils.dates import MONTHS, WEEKDAYS, WEEKDAYS_ABBR
from django.utils.translation import get_language
from django.utils.translation import gettext as _

# Wagtail languages with >=90% coverage
# This list is manually maintained
WAGTAILADMIN_PROVIDED_LANGUAGES = [
    ("ar", "Arabic"),
    ("ca", "Catalan"),
    ("cs", "Czech"),
    ("de", "German"),
    ("el", "Greek"),
    ("en", "English"),
    ("es", "Spanish"),
    ("et", "Estonian"),
    ("fi", "Finnish"),
    ("fr", "French"),
    ("gl", "Galician"),
    ("hr", "Croatian"),
    ("hu", "Hungarian"),
    ("id-id", "Indonesian"),
    ("is-is", "Icelandic"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("lt", "Lithuanian"),
    ("mn", "Mongolian"),
    ("nb", "Norwegian Bokmål"),
    ("nl", "Dutch"),
    ("fa", "Persian"),
    ("pl", "Polish"),
    ("pt-br", "Brazilian Portuguese"),
    ("pt-pt", "Portuguese"),
    ("ro", "Romanian"),
    ("ru", "Russian"),
    ("sv", "Swedish"),
    ("sk-sk", "Slovak"),
    ("sl", "Slovenian"),
    ("th", "Thai"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("zh-hans", "Chinese (Simplified)"),
    ("zh-hant", "Chinese (Traditional)"),
]

if DJANGO_VERSION >= (5, 0):
    WAGTAILADMIN_PROVIDED_LANGUAGES.append(("ug", "Uyghur"))
    WAGTAILADMIN_PROVIDED_LANGUAGES.sort()


# Translatable strings to be made available to JavaScript code
# as the wagtailConfig.STRINGS object
def get_js_translation_strings():
    return {
        "MONTHS": [str(m) for m in MONTHS.values()],
        # Django's WEEKDAYS list begins on Monday, but ours should start on Sunday, so start
        # counting from -1 and use modulo 7 to get an array index
        "WEEKDAYS": [str(WEEKDAYS[d % 7]) for d in range(-1, 6)],
        "WEEKDAYS_SHORT": [str(WEEKDAYS_ABBR[d % 7]) for d in range(-1, 6)],
        # used by bulk actions
        "BULK_ACTIONS": {
            "PAGE": {
                "SINGULAR": _("1 page selected"),
                "PLURAL": _("%(objects)s pages selected"),
                "ALL": _("All %(objects)s pages on this screen selected"),
                "ALL_IN_LISTING": _("All pages in listing selected"),
            },
            "DOCUMENT": {
                "SINGULAR": _("1 document selected"),
                "PLURAL": _("%(objects)s documents selected"),
                "ALL": _("All %(objects)s documents on this screen selected"),
                "ALL_IN_LISTING": _("All documents in listing selected"),
            },
            "IMAGE": {
                "SINGULAR": _("1 image selected"),
                "PLURAL": _("%(objects)s images selected"),
                "ALL": _("All %(objects)s images on this screen selected"),
                "ALL_IN_LISTING": _("All images in listing selected"),
            },
            "USER": {
                "SINGULAR": _("1 user selected"),
                "PLURAL": _("%(objects)s users selected"),
                "ALL": _("All %(objects)s users on this screen selected"),
                "ALL_IN_LISTING": _("All users in listing selected"),
            },
            "SNIPPET": {
                "SINGULAR": _("1 snippet selected"),
                "PLURAL": _("%(objects)s snippets selected"),
                "ALL": _("All %(objects)s snippets on this screen selected"),
                "ALL_IN_LISTING": _("All snippets in listing selected"),
            },
            "ITEM": {
                "SINGULAR": _("1 item selected"),
                "PLURAL": _("%(objects)s items selected"),
                "ALL": _("All %(objects)s items on this screen selected"),
                "ALL_IN_LISTING": _("All items in listing selected"),
            },
        },
    }


def get_available_admin_languages():
    return getattr(
        settings, "WAGTAILADMIN_PERMITTED_LANGUAGES", WAGTAILADMIN_PROVIDED_LANGUAGES
    )


@functools.cache
def get_available_admin_time_zones():
    if not settings.USE_TZ:
        return []

    return getattr(
        settings, "WAGTAIL_USER_TIME_ZONES", sorted(zoneinfo.available_timezones())
    )


def gettext_domain(domain: str, message: str) -> str:
    """
    Similar to Django's ``gettext``, return the translation for a specific
    domain (i.e. a specific ``.po`` file).
    """
    if settings.USE_I18N:
        # Get current language, and fallback to non-specific version of language.
        langs = [get_language()] + [get_language().split("-")[0]]
        lc_path = os.path.join(os.path.dirname(__file__), "locale")
        _gt = gettext.translation(
            domain,
            localedir=lc_path,
            languages=langs,
            fallback=True,
        )
        return _gt.gettext(message)
    return message
