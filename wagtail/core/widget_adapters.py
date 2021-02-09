"""
Register Telepath adapters for core Django form widgets, so that they can
have corresponding Javascript objects with the ability to render new instances
and extract field values.
"""

from django import forms
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.telepath import Adapter, register


class WidgetAdapter(Adapter):
    js_constructor = 'wagtail.widgets.Widget'

    def js_args(self, widget):
        return [
            widget.render('__NAME__', None, attrs={'id': '__ID__'}),
            widget.id_for_label('__ID__'),
        ]

    def get_media(self, widget):
        media = super().get_media(widget)
        return media + widget.media

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/telepath/widgets.js'),
        ])


register(WidgetAdapter(), forms.widgets.Input)
register(WidgetAdapter(), forms.Textarea)
register(WidgetAdapter(), forms.Select)


class RadioSelectAdapter(WidgetAdapter):
    js_constructor = 'wagtail.widgets.RadioSelect'


register(RadioSelectAdapter(), forms.RadioSelect)
