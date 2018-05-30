import json

from django.forms import Media, widgets

from wagtail.admin.edit_handlers import RichTextFieldPanel
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.core.rich_text import features as feature_registry
from wagtail.utils.widgets import WidgetWithScript


class DraftailRichTextArea(WidgetWithScript, widgets.HiddenInput):
    # this class's constructor accepts a 'features' kwarg
    accepts_features = True

    def get_panel(self):
        return RichTextFieldPanel

    def __init__(self, *args, **kwargs):
        # note: this constructor will receive an 'options' kwarg taken from the WAGTAILADMIN_RICH_TEXT_EDITORS setting,
        # but we don't currently recognise any options from there (other than 'features', which is passed here as a separate kwarg)
        kwargs.pop('options', None)
        self.options = {}

        self._media = Media(js=[
            'wagtailadmin/js/draftail.js',
        ], css={
            'all': ['wagtailadmin/css/panels/draftail.css']
        })

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.features = feature_registry.get_default_features()

        for feature in self.features:
            plugin = feature_registry.get_editor_plugin('draftail', feature)
            if plugin:
                plugin.construct_options(self.options)
                self._media += plugin.media

        self.converter = ContentstateConverter(self.features)

        super().__init__(*args, **kwargs)

    def translate_value(self, value):
        # Convert database rich text representation to the format required by
        # the input field

        if value is None:
            value = ''

        return self.converter.from_database_format(value)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}

        attrs['data-draftail-input'] = True

        translated_value = self.translate_value(value)
        return super().render(name, translated_value, attrs)

    def render_js_init(self, id_, name, value):
        return "window.draftail.initEditor('#{id}', {opts}, document.currentScript)".format(
            id=id_, opts=json.dumps(self.options))

    def value_from_datadict(self, data, files, name):
        original_value = super().value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return self.converter.to_database_format(original_value)

    @property
    def media(self):
        return self._media
