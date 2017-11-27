import json
from collections import OrderedDict

from django.conf import settings
from django.forms import Media, widgets
from django.utils.module_loading import import_string

from wagtail.utils.widgets import WidgetWithScript
from wagtail.admin.edit_handlers import RichTextFieldPanel
from wagtail.core.rich_text import DbWhitelister, expand_db_html, features


class HalloPlugin:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.options = kwargs.get('options', {})
        self.js = kwargs.get('js', None)
        self.css = kwargs.get('css', None)
        self.order = kwargs.get('order', 100)

    def construct_plugins_list(self, plugins):
        if self.name is not None:
            plugins[self.name] = self.options

    @property
    def media(self):
        return Media(js=self.js, css=self.css)


class HalloFormatPlugin(HalloPlugin):
    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'halloformat')
        kwargs.setdefault('order', 10)
        self.format_name = kwargs['format_name']
        super().__init__(**kwargs)

    def construct_plugins_list(self, plugins):
        plugins.setdefault(self.name, {'formattings': {
            'bold': False, 'italic': False, 'strikeThrough': False, 'underline': False
        }})
        plugins[self.name]['formattings'][self.format_name] = True


class HalloHeadingPlugin(HalloPlugin):
    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'halloheadings')
        kwargs.setdefault('order', 20)
        self.element = kwargs.pop('element')
        super().__init__(**kwargs)

    def construct_plugins_list(self, plugins):
        plugins.setdefault(self.name, {'formatBlocks': []})
        plugins[self.name]['formatBlocks'].append(self.element)


class HalloListPlugin(HalloPlugin):
    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'hallolists')
        kwargs.setdefault('order', 40)
        self.list_type = kwargs['list_type']
        super().__init__(**kwargs)

    def construct_plugins_list(self, plugins):
        plugins.setdefault(self.name, {'lists': {
            'ordered': False, 'unordered': False
        }})
        plugins[self.name]['lists'][self.list_type] = True


# Plugins which are always imported, and cannot be enabled/disabled via 'features'
CORE_HALLO_PLUGINS = [
    HalloPlugin(name='halloreundo', order=50),
    HalloPlugin(name='hallorequireparagraphs', js=[
        'wagtailadmin/js/hallo-plugins/hallo-requireparagraphs.js',
    ]),
    HalloHeadingPlugin(element='p')
]


class HalloRichTextArea(WidgetWithScript, widgets.Textarea):
    # this class's constructor accepts a 'features' kwarg
    accepts_features = True

    def get_panel(self):
        return RichTextFieldPanel

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', None)

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.features = features.get_default_features()

        # construct a list of plugin objects, by querying the feature registry
        # and keeping the non-null responses from get_editor_plugin
        self.plugins = CORE_HALLO_PLUGINS + list(filter(None, [
            features.get_editor_plugin('hallo', feature_name)
            for feature_name in self.features
        ]))
        self.plugins.sort(key=lambda plugin: plugin.order)

        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            translated_value = None
        else:
            translated_value = expand_db_html(value, for_editor=True)
        return super().render(name, translated_value, attrs)

    def render_js_init(self, id_, name, value):
        if self.options is not None and 'plugins' in self.options:
            # explicit 'plugins' config passed in options, so use that
            plugin_data = self.options['plugins']
        else:
            plugin_data = OrderedDict()
            for plugin in self.plugins:
                plugin.construct_plugins_list(plugin_data)

        return "makeHalloRichTextEditable({0}, {1});".format(
            json.dumps(id_), json.dumps(plugin_data)
        )

    def value_from_datadict(self, data, files, name):
        original_value = super().value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return DbWhitelister.clean(original_value)

    @property
    def media(self):
        media = Media(js=[
            'wagtailadmin/js/vendor/hallo.js',
            'wagtailadmin/js/hallo-bootstrap.js',
        ])

        for plugin in self.plugins:
            media += plugin.media

        return media


DEFAULT_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.HalloRichTextArea'
    }
}


def get_rich_text_editor_widget(name='default', features=None):
    editor_settings = getattr(settings, 'WAGTAILADMIN_RICH_TEXT_EDITORS', DEFAULT_RICH_TEXT_EDITORS)

    editor = editor_settings[name]
    options = editor.get('OPTIONS', None)

    if features is None and options is not None:
        # fall back on 'features' list within OPTIONS, if any
        features = options.get('features', None)

    cls = import_string(editor['WIDGET'])

    kwargs = {}

    if options is not None:
        kwargs['options'] = options

    if getattr(cls, 'accepts_features', False):
        kwargs['features'] = features

    return cls(**kwargs)
