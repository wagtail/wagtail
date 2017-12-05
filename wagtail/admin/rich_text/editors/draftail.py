import json

from django.forms import Media, widgets

from wagtail.admin.edit_handlers import RichTextFieldPanel
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.core.rich_text import features


class DraftailRichTextArea(widgets.Textarea):
    # this class's constructor accepts a 'features' kwarg
    accepts_features = True

    def get_panel(self):
        return RichTextFieldPanel

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', None)

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.features = features.get_default_features()

        self.converter = ContentstateConverter(self.features)

        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            translated_value = None
        else:
            translated_value = self.converter.from_database_format(value)
        return super().render(name, translated_value, attrs)

    def render_js_init(self, id_, name, value):
        return "window.draftail.initEditor('{name}', {opts})".format(
            name=name, opts=json.dumps(self.options))

    def value_from_datadict(self, data, files, name):
        original_value = super().value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return self.converter.to_database_format(original_value)

    @property
    def media(self):
        return Media(js=[
            'wagtailadmin/js/draftail.js',
        ], css={
            'all': ['wagtailadmin/css/panels/dratail.css']
        })
