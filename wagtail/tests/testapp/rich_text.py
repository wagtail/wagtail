from __future__ import absolute_import, unicode_literals

import json

from django.forms import widgets, Media
from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel

from wagtail.utils.widgets import WidgetWithScript


class CustomRichTextArea(WidgetWithScript, widgets.Textarea):
    def get_panel(self):
        return RichTextFieldPanel

    def render_js_init(self, id_, name, value):
        return "customEditorInitScript({0});".format(json.dumps(id_))

    @property
    def media(self):
        return Media(js=[
            'vendor/custom_editor.js'
        ])
