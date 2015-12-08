from __future__ import absolute_import

try:
    import jinja2
    from jinja2.ext import Extension
except:
    Extension = object

from .wagtailuserbar import wagtailuserbar


class WagtailUserbarExtension(Extension):
    def __init__(self, environment):
        super(WagtailUserbarExtension, self).__init__(environment)

        self.environment.globals.update({
            'wagtailuserbar': jinja2.contextfunction(wagtailuserbar),
        })


# Nicer import names
userbar = WagtailUserbarExtension
