from __future__ import unicode_literals

from six import text_type

from django.utils.text import slugify
from django.utils.html import format_html


class MenuItem(object):
    def __init__(self, label, url, name=None, classnames='', order=1000):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(text_type(label)))
        self.order = order

    def render_html(self):
        return format_html(
            """<li class="menu-{0}"><a href="{1}" class="{2}">{3}</a></li>""",
            self.name, self.url, self.classnames, self.label)
