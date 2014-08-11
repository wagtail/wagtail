from __future__ import unicode_literals

from six import text_type

try:
    # renamed util -> utils in Django 1.7; try the new name first
    from django.forms.utils import flatatt
except ImportError:
    from django.forms.util import flatatt

from django.utils.text import slugify
from django.utils.html import format_html


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

    def render_html(self):
        return format_html(
            """<li class="menu-{0}"><a href="{1}" class="{2}"{3}>{4}</a></li>""",
            self.name, self.url, self.classnames, self.attr_string, self.label)
