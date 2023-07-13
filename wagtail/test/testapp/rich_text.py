import json

from django.forms import Media, widgets

from wagtail.utils.widgets import WidgetWithScript


class CustomRichTextArea(WidgetWithScript, widgets.Textarea):
    def render_js_init(self, id_, name, value):
        return f"customEditorInitScript({json.dumps(id_)});"

    @property
    def media(self):
        return Media(js=["vendor/custom_editor.js"])


class LegacyRichTextArea(WidgetWithScript, widgets.Textarea):
    def render_js_init(self, id_, name, value):
        return f"legacyEditorInitScript({json.dumps(id_)});"

    @property
    def media(self):
        return Media(js=["vendor/legacy_editor.js"])
