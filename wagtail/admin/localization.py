import pytz
from django.conf import settings
from django.utils.dates import MONTHS, WEEKDAYS, WEEKDAYS_ABBR
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
    ("th", "Thai"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("zh-hans", "Chinese (Simplified)"),
    ("zh-hant", "Chinese (Traditional)"),
]


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
                "PLURAL": _("{0} pages selected"),
                "ALL": _("All {0} pages on this screen selected"),
                "ALL_IN_LISTING": _("All pages in listing selected"),
            },
            "DOCUMENT": {
                "SINGULAR": _("1 document selected"),
                "PLURAL": _("{0} documents selected"),
                "ALL": _("All {0} documents on this screen selected"),
                "ALL_IN_LISTING": _("All documents in listing selected"),
            },
            "IMAGE": {
                "SINGULAR": _("1 image selected"),
                "PLURAL": _("{0} images selected"),
                "ALL": _("All {0} images on this screen selected"),
                "ALL_IN_LISTING": _("All images in listing selected"),
            },
            "USER": {
                "SINGULAR": _("1 user selected"),
                "PLURAL": _("{0} users selected"),
                "ALL": _("All {0} users on this screen selected"),
                "ALL_IN_LISTING": _("All users in listing selected"),
            },
            "SNIPPET": {
                "SINGULAR": _("1 snippet selected"),
                "PLURAL": _("{0} snippets selected"),
                "ALL": _("All {0} snippets on this screen selected"),
                "ALL_IN_LISTING": _("All snippets in listing selected"),
            },
            "ITEM": {
                "SINGULAR": _("1 item selected"),
                "PLURAL": _("{0} items selected"),
                "ALL": _("All {0} items on this screen selected"),
                "ALL_IN_LISTING": _("All items in listing selected"),
            },
        },
    }


def get_available_admin_languages():
    return getattr(
        settings, "WAGTAILADMIN_PERMITTED_LANGUAGES", WAGTAILADMIN_PROVIDED_LANGUAGES
    )


def get_available_admin_time_zones():
    if not settings.USE_TZ:
        return []

    return getattr(settings, "WAGTAIL_USER_TIME_ZONES", pytz.common_timezones)
