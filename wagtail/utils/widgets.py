from django.forms.widgets import Widget
from django.utils.safestring import mark_safe


class WidgetWithScript(Widget):
    def render_html(self, name, value, attrs):
        """Render the HTML (non-JS) portion of the field markup"""
        return super().render(name, value, attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # no point trying to come up with sensible semantics for when 'id' is missing from attrs,
        # so let's make sure it fails early in the process
        try:
            id_ = attrs['id']
        except (KeyError, TypeError):
            raise TypeError("WidgetWithScript cannot be rendered without an 'id' attribute")

        widget_html = self.render_html(name, value, attrs)

        js = self.render_js_init(id_, name, value)
        out = '{0}<script>{1}</script>'.format(widget_html, js)
        return mark_safe(out)

    def render_js_init(self, id_, name, value):
        return ''
