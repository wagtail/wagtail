import pytz

from django.conf import settings
from django.utils.dates import MONTHS, WEEKDAYS, WEEKDAYS_ABBR
from django.utils.translation import gettext as _


# Wagtail languages with >=90% coverage
# This list is manually maintained
WAGTAILADMIN_PROVIDED_LANGUAGES = [
    ('ar', 'Arabic'),
    ('ca', 'Catalan'),
    ('cs', 'Czech'),
    ('de', 'German'),
    ('el', 'Greek'),
    ('en', 'English'),
    ('es', 'Spanish'),
    ('et', 'Estonian'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('gl', 'Galician'),
    ('hr', 'Croatian'),
    ('hu', 'Hungarian'),
    ('id-id', 'Indonesian'),
    ('is-is', 'Icelandic'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('lt', 'Lithuanian'),
    ('mn', 'Mongolian'),
    ('nb', 'Norwegian Bokmål'),
    ('nl', 'Dutch'),
    ('fa', 'Persian'),
    ('pl', 'Polish'),
    ('pt-br', 'Brazilian Portuguese'),
    ('pt-pt', 'Portuguese'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('sv', 'Swedish'),
    ('sk-sk', 'Slovak'),
    ('th', 'Thai'),
    ('tr', 'Turkish'),
    ('uk', 'Ukrainian'),
    ('zh-hans', 'Chinese (Simplified)'),
    ('zh-hant', 'Chinese (Traditional)'),
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
        'DECORATIVE_IMAGE': _('Decorative image'),
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
        'SAVE': _('Save'),
        'SAVING': _('Saving...'),
        'CANCEL': _('Cancel'),
        'DELETING': _('Deleting...'),
        'ADD_A_COMMENT': _('Add a comment'),
        'SHOW_COMMENTS': _('Show comments'),
        'REPLY': _('Reply'),
        'RESOLVE': _('Resolve'),
        'RETRY': _('Retry'),
        'DELETE_ERROR': _('Delete error'),
        'CONFIRM_DELETE_COMMENT': _('Are you sure?'),
        'SAVE_ERROR': _('Save error'),
        'SAVE_COMMENT_WARNING': _('This will be saved when the page is saved'),
        'FOCUS_COMMENT': _('Focus comment'),
        'UNFOCUS_COMMENT': _('Unfocus comment'),
        'COMMENT': _('Comment'),
        'MORE_ACTIONS': _('More actions'),
        'SAVE_PAGE_TO_ADD_COMMENT': _('Save the page to add this comment'),
        'SAVE_PAGE_TO_SAVE_COMMENT_CHANGES': _('Save the page to save this comment'),
        'SAVE_PAGE_TO_SAVE_REPLY': _('Save the page to save this reply'),
        'DASHBOARD': _('Dashboard'),
        'EDIT_YOUR_ACCOUNT': _('Edit your account'),
        'SEARCH': _('Search'),

        'MONTHS': [str(m) for m in MONTHS.values()],

        # Django's WEEKDAYS list begins on Monday, but ours should start on Sunday, so start
        # counting from -1 and use modulo 7 to get an array index
        'WEEKDAYS': [str(WEEKDAYS[d % 7]) for d in range(-1, 6)],
        'WEEKDAYS_SHORT': [str(WEEKDAYS_ABBR[d % 7]) for d in range(-1, 6)],

        # used by bulk actions
        'BULK_ACTIONS': {
            'PAGE': {
                'SINGULAR': _('1 page selected'),
                'PLURAL': _("{0} pages selected"),
                'ALL': _("All {0} pages on this screen selected"),
                'ALL_IN_LISTING': _("All pages in listing selected"),
            },
            'DOCUMENT': {
                'SINGULAR': _('1 document selected'),
                'PLURAL': _("{0} documents selected"),
                'ALL': _("All {0} documents on this screen selected"),
                'ALL_IN_LISTING': _("All documents in listing selected"),
            },
            'IMAGE': {
                'SINGULAR': _('1 image selected'),
                'PLURAL': _("{0} images selected"),
                'ALL': _("All {0} images on this screen selected"),
                'ALL_IN_LISTING': _("All images in listing selected"),
            },
            'USER': {
                'SINGULAR': _('1 user selected'),
                'PLURAL': _("{0} users selected"),
                'ALL': _("All {0} users on this screen selected"),
                'ALL_IN_LISTING': _("All users in listing selected"),
            },
            'ITEM': {
                'SINGULAR': _('1 item selected'),
                'PLURAL': _("{0} items selected"),
                'ALL': _("All {0} items on this screen selected"),
                'ALL_IN_LISTING': _("All items in listing selected"),
            },
        },
    }


def get_available_admin_languages():
    return getattr(settings, 'WAGTAILADMIN_PERMITTED_LANGUAGES', WAGTAILADMIN_PROVIDED_LANGUAGES)


def get_available_admin_time_zones():
    if not settings.USE_TZ:
        return []

    return getattr(settings, 'WAGTAIL_USER_TIME_ZONES', pytz.common_timezones)
