import jinja2
from jinja2.ext import Extension



class WagtailUserbarExtension(Extension):
    def __init__(self, environment):
        from .templatetags.wagtailuserbar import wagtailuserbar

        super().__init__(environment)

        self.environment.globals.update(
            {
                "wagtailuserbar": jinja2.pass_context(wagtailuserbar),
            }
        )


# Nicer import names
userbar = WagtailUserbarExtension
