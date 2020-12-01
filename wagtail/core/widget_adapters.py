"""
Register Telepath adapters for core Django form widgets, so that they can
have corresponding Javascript objects with the ability to render new instances
and extract field values.
"""

from django import forms

from wagtail.core.telepath import Adapter, register


class WidgetAdapter(Adapter):
    js_constructor = 'wagtail.widgets.Widget'

    def js_args(self, widget, context):
        return [
            widget.render('__NAME__', None, attrs={'id': '__ID__'}),
            widget.id_for_label('__ID__'),
        ]

    class Media:
        # FIXME: where does the widget's own media get merged in? Probably here,
        # but in that case we need this to be a method that receives the object as
        # a parameter, like js_args
        js = ['wagtailadmin/js/telepath/widgets.js']


register(WidgetAdapter(), forms.widgets.Input)
register(WidgetAdapter(), forms.Textarea)
register(WidgetAdapter(), forms.Select)


class RadioSelectAdapter(WidgetAdapter):
    js_constructor = 'wagtail.widgets.RadioSelect'


register(RadioSelectAdapter(), forms.RadioSelect)
