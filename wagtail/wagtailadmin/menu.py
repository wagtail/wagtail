from __future__ import unicode_literals

from six import text_type

try:
    # renamed util -> utils in Django 1.7; try the new name first
    from django.forms.utils import flatatt
except ImportError:
    from django.forms.util import flatatt

from django.conf import settings
from django.utils.text import slugify
from django.utils.html import format_html, format_html_join

from wagtail.wagtailcore import hooks


class MenuItem(object):
    def __init__(self, label, url, name=None, classnames='', attrs=None, order=1000):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(text_type(label)))
        self.order = order

        if attrs:
            self.attr_string = flatatt(attrs)
        else:
            self.attr_string = ""

    js_files = []
    def render_js(self):
        """
        Return a string of any Javascript declarations required by this menu item.
        These will be included on all admin pages, regardless of whether the menu item
        is actually shown or not - this allows us to cache/compress the JS globally.
        By default this returns a script tag for every file listed in self.js_files.
        """
        if self.js_files:
            return format_html_join('\n', '<script src="{0}{1}"></script>',
                    ((settings.STATIC_URL, filename) for filename in self.js_files)
                )

    def is_shown(self, request):
        """
        Whether this menu item should be shown for the given request; permission
        checks etc should go here. By default, menu items are shown all the time
        """
        return True

    def render_html(self):
        return format_html(
            """<li class="menu-{0}"><a href="{1}" class="{2}"{3}>{4}</a></li>""",
            self.name, self.url, self.classnames, self.attr_string, self.label)


_master_menu_item_list = None
def get_master_menu_item_list():
    """
    Return the list of menu items registered with the 'register_admin_menu_item' hook.
    This is the "master list" because the final admin menu may vary per request
    according to the value of is_shown() and the construct_main_menu hook.
    """
    global _master_menu_item_list
    if _master_menu_item_list is None:
        _master_menu_item_list = [fn() for fn in hooks.get_hooks('register_admin_menu_item')]

    return _master_menu_item_list
