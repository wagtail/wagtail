from warnings import warn

from django.forms.widgets import Widget
from django.utils.safestring import mark_safe

from wagtail.utils.deprecation import RemovedInWagtail70Warning


class WidgetWithScript(Widget):
    warn(
        "The usage of `WidgetWithScript` hook is deprecated. Use external scripts instead.",
        category=RemovedInWagtail70Warning,
        stacklevel=3,
    )

    def render_html(self, name, value, attrs):
        """Render the HTML (non-JS) portion of the field markup"""
        return super().render(name, value, attrs)

    def get_value_data(self, value):
        # Perform any necessary preprocessing on the value passed to render() before it is passed
        # on to render_html / render_js_init. This is a good place to perform database lookups
        # that are needed by both render_html and render_js_init. Return value is arbitrary
        # (we only care that render_html / render_js_init can accept it), but will typically be
        # a dict of data needed for rendering: id, title etc.
        return value

    def render(self, name, value, attrs=None, renderer=None):
        # no point trying to come up with sensible semantics for when 'id' is missing from attrs,
        # so let's make sure it fails early in the process
        try:
            id_ = attrs["id"]
        except (KeyError, TypeError):
            raise TypeError(
                "WidgetWithScript cannot be rendered without an 'id' attribute"
            )

        value_data = self.get_value_data(value)
        widget_html = self.render_html(name, value_data, attrs)

        js = self.render_js_init(id_, name, value_data)
        out = f"{widget_html}<script>{js}</script>"
        return mark_safe(out)

    def render_js_init(self, id_, name, value):
        return ""
