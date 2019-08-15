import pytz

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy


# Wagtail languages with >=90% coverage
# This list is manually maintained
WAGTAILADMIN_PROVIDED_LANGUAGES = [
    ('ar', ugettext_lazy('Arabic')),
    ('ca', ugettext_lazy('Catalan')),
    ('cs', ugettext_lazy('Czech')),
    ('de', ugettext_lazy('German')),
    ('el', ugettext_lazy('Greek')),
    ('en', ugettext_lazy('English')),
    ('es', ugettext_lazy('Spanish')),
    ('fi', ugettext_lazy('Finnish')),
    ('fr', ugettext_lazy('French')),
    ('gl', ugettext_lazy('Galician')),
    ('hu', ugettext_lazy('Hungarian')),
    ('id-id', ugettext_lazy('Indonesian')),
    ('is-is', ugettext_lazy('Icelandic')),
    ('it', ugettext_lazy('Italian')),
    ('jp', ugettext_lazy('Japanese')),
    ('ko', ugettext_lazy('Korean')),
    ('lt', ugettext_lazy('Lithuanian')),
    ('mn', ugettext_lazy('Mongolian')),
    ('nb', ugettext_lazy('Norwegian Bokmål')),
    ('nl-nl', ugettext_lazy('Netherlands Dutch')),
    ('fa', ugettext_lazy('Persian')),
    ('pl', ugettext_lazy('Polish')),
    ('pt-br', ugettext_lazy('Brazilian Portuguese')),
    ('pt-pt', ugettext_lazy('Portuguese')),
    ('ro', ugettext_lazy('Romanian')),
    ('ru', ugettext_lazy('Russian')),
    ('sv', ugettext_lazy('Swedish')),
    ('sk-sk', ugettext_lazy('Slovak')),
    ('th', ugettext_lazy('Thai')),
    ('uk', ugettext_lazy('Ukrainian')),
    ('zh-hans', ugettext_lazy('Chinese (Simplified)')),
    ('zh-hant', ugettext_lazy('Chinese (Traditional)')),
]


# Translatable strings to be made available to Javascript code
# as the wagtailConfig.STRINGS object
def get_js_translation_strings():
    return {
        'DELETE': _('Delete'),
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

        'MONTHS': [
            _('January'),
            _('February'),
            _('March'),
            _('April'),
            _('May'),
            _('June'),
            _('July'),
            _('August'),
            _('September'),
            _('October'),
            _('November'),
            _('December')
        ],
        'WEEKDAYS': [
            _('Sunday'),
            _('Monday'),
            _('Tuesday'),
            _('Wednesday'),
            _('Thursday'),
            _('Friday'),
            _('Saturday')
        ],
        'WEEKDAYS_SHORT': [
            _('Sun'),
            _('Mon'),
            _('Tue'),
            _('Wed'),
            _('Thu'),
            _('Fri'),
            _('Sat')
        ]
    }


def get_available_admin_languages():
    return getattr(settings, 'WAGTAILADMIN_PERMITTED_LANGUAGES', WAGTAILADMIN_PROVIDED_LANGUAGES)


def get_available_admin_time_zones():
    return getattr(settings, 'WAGTAIL_USER_TIME_ZONES', pytz.common_timezones)
