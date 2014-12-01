from __future__ import absolute_import, unicode_literals

from django.forms.widgets import Widget
from django.utils.safestring import mark_safe


class WidgetWithScript(Widget):
    def render(self, name, value, attrs=None):
        widget = super(WidgetWithScript, self).render(name, value, attrs)

        final_attrs = self.build_attrs(attrs, name=name)
        id_ = final_attrs.get('id', None)
        if id_ is None:
            return widget

        js = self.render_js_init(id_, name, value)
        out = '{0}<script>{1}</script>'.format(widget, js)
        return mark_safe(out)

    def render_js_init(self, id_, name, value):
        return ''
