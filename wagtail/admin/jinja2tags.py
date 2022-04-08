import jinja2
from jinja2.ext import Extension

from .templatetags.wagtailuserbar import wagtailuserbar


class WagtailUserbarExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update(
            {
                "wagtailuserbar": jinja2.pass_context(wagtailuserbar),
            }
        )


# Nicer import names
userbar = WagtailUserbarExtension
