import pytz

from django.conf import settings
from django.utils.dates import MONTHS, WEEKDAYS, WEEKDAYS_ABBR
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy


# Wagtail languages with >=90% coverage
# This list is manually maintained
WAGTAILADMIN_PROVIDED_LANGUAGES = [
    ('ar', gettext_lazy('Arabic')),
    ('ca', gettext_lazy('Catalan')),
    ('cs', gettext_lazy('Czech')),
    ('de', gettext_lazy('German')),
    ('el', gettext_lazy('Greek')),
    ('en', gettext_lazy('English')),
    ('es', gettext_lazy('Spanish')),
    ('et', gettext_lazy('Estonian')),
    ('fi', gettext_lazy('Finnish')),
    ('fr', gettext_lazy('French')),
    ('gl', gettext_lazy('Galician')),
    ('hr', gettext_lazy('Croatian')),
    ('hu', gettext_lazy('Hungarian')),
    ('id-id', gettext_lazy('Indonesian')),
    ('is-is', gettext_lazy('Icelandic')),
    ('it', gettext_lazy('Italian')),
    ('ja', gettext_lazy('Japanese')),
    ('ko', gettext_lazy('Korean')),
    ('lt', gettext_lazy('Lithuanian')),
    ('mn', gettext_lazy('Mongolian')),
    ('nb', gettext_lazy('Norwegian Bokmål')),
    ('nl-nl', gettext_lazy('Netherlands Dutch')),
    ('fa', gettext_lazy('Persian')),
    ('pl', gettext_lazy('Polish')),
    ('pt-br', gettext_lazy('Brazilian Portuguese')),
    ('pt-pt', gettext_lazy('Portuguese')),
    ('ro', gettext_lazy('Romanian')),
    ('ru', gettext_lazy('Russian')),
    ('sv', gettext_lazy('Swedish')),
    ('sk-sk', gettext_lazy('Slovak')),
    ('th', gettext_lazy('Thai')),
    ('tr', gettext_lazy('Turkish')),
    ('tr-tr', gettext_lazy('Turkish (Turkey)')),
    ('uk', gettext_lazy('Ukrainian')),
    ('zh-hans', gettext_lazy('Chinese (Simplified)')),
    ('zh-hant', gettext_lazy('Chinese (Traditional)')),
]


# Translatable strings to be made available to JavaScript code
# as the wagtailConfig.STRINGS object
def get_js_translation_strings():
    return {
        'DELETE': _('Delete'),
        'EDIT': _('Edit'),
        'PAGE': _('Page'),
        'PAGES': _('Pages'),
        'LOADING': _('Loading…'),
        'NO_RESULTS': _('No results'),
        'SERVER_ERROR': _('Server Error'),
        'SEE_ALL': _('See all'),
        'CLOSE_EXPLORER': _('Close explorer'),
        'ALT_TEXT': _('Alt text'),
        'WRITE_HERE': _('Write here…'),
        'HORIZONTAL_LINE': _('Horizontal line'),
        'LINE_BREAK': _('Line break'),
        'UNDO': _('Undo'),
        'REDO': _('Redo'),
        'RELOAD_PAGE': _('Reload the page'),
        'RELOAD_EDITOR': _('Reload saved content'),
        'SHOW_LATEST_CONTENT': _('Show latest content'),
        'SHOW_ERROR': _('Show error'),
        'EDITOR_CRASH': _('The editor just crashed. Content has been reset to the last saved version.'),
        'BROKEN_LINK': _('Broken link'),
        'MISSING_DOCUMENT': _('Missing document'),
        'CLOSE': _('Close'),
        'EDIT_PAGE': _('Edit \'{title}\''),
        'VIEW_CHILD_PAGES_OF_PAGE': _('View child pages of \'{title}\''),
        'PAGE_EXPLORER': _('Page explorer'),

        'MONTHS': [str(m) for m in MONTHS.values()],

        # Django's WEEKDAYS list begins on Monday, but ours should start on Sunday, so start
        # counting from -1 and use modulo 7 to get an array index
        'WEEKDAYS': [str(WEEKDAYS[d % 7]) for d in range(-1, 6)],
        'WEEKDAYS_SHORT': [str(WEEKDAYS_ABBR[d % 7]) for d in range(-1, 6)],
    }


def get_available_admin_languages():
    return getattr(settings, 'WAGTAILADMIN_PERMITTED_LANGUAGES', WAGTAILADMIN_PROVIDED_LANGUAGES)


def get_available_admin_time_zones():
    return getattr(settings, 'WAGTAIL_USER_TIME_ZONES', pytz.common_timezones)
