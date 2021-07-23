import json

from collections import OrderedDict

from django.forms import Media, widgets
from django.utils.functional import cached_property

from wagtail.admin.edit_handlers import RichTextFieldPanel
from wagtail.admin.rich_text.converters.editor_html import EditorHTMLConverter
from wagtail.admin.staticfiles import versioned_static
from wagtail.core.rich_text import features
from wagtail.core.telepath import register
from wagtail.core.widget_adapters import WidgetAdapter


class HalloPlugin:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.options = kwargs.get('options', {})
        self.js = kwargs.get('js', [])
        self.css = kwargs.get('css', {})
        self.order = kwargs.get('order', 100)

    def construct_plugins_list(self, plugins):
        if self.name is not None:
            plugins[self.name] = self.options

    @property
    def media(self):
        js = [versioned_static(js_file) for js_file in self.js]
        css = {}
        for media_type, css_files in self.css.items():
            css[media_type] = [versioned_static(css_file) for css_file in css_files]

        return Media(js=js, css=css)


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
    default_order = 20

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'halloheadings')
        kwargs.setdefault('order', self.default_order)
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


class HalloRequireParagraphsPlugin(HalloPlugin):
    @property
    def media(self):
        return Media(js=[
            versioned_static('wagtailadmin/js/hallo-plugins/hallo-requireparagraphs.js'),
        ]) + super().media


# Plugins which are always imported, and cannot be enabled/disabled via 'features'
CORE_HALLO_PLUGINS = [
    HalloPlugin(name='halloreundo', order=50),
    HalloRequireParagraphsPlugin(name='hallorequireparagraphs'),
    HalloHeadingPlugin(element='p')
]


class HalloRichTextArea(widgets.Textarea):
    template_name = 'wagtailadmin/widgets/hallo_rich_text_area.html'

    # this class's constructor accepts a 'features' kwarg
    accepts_features = True

    def get_panel(self):
        return RichTextFieldPanel

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', None)

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.features = features.get_default_features()

        self.converter = EditorHTMLConverter(self.features)

        # construct a list of plugin objects, by querying the feature registry
        # and keeping the non-null responses from get_editor_plugin
        self.plugins = CORE_HALLO_PLUGINS + list(filter(None, [
            features.get_editor_plugin('hallo', feature_name)
            for feature_name in self.features
        ]))
        self.plugins.sort(key=lambda plugin: plugin.order)

        super().__init__(*args, **kwargs)

    def format_value(self, value):
        # Convert database rich text representation to the format required by
        # the input field
        value = super().format_value(value)

        if value is None:
            return None

        return self.converter.from_database_format(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if self.options is not None and 'plugins' in self.options:
            # explicit 'plugins' config passed in options, so use that
            plugin_data = self.options['plugins']
        else:
            plugin_data = OrderedDict()
            for plugin in self.plugins:
                plugin.construct_plugins_list(plugin_data)
        context['widget']['plugins_json'] = json.dumps(plugin_data)

        return context

    def value_from_datadict(self, data, files, name):
        original_value = super().value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return self.converter.to_database_format(original_value)

    @cached_property
    def media(self):
        media = Media(js=[
            versioned_static('wagtailadmin/js/vendor/hallo.js'),
            versioned_static('wagtailadmin/js/hallo-bootstrap.js'),
        ], css={
            'all': [versioned_static('wagtailadmin/css/panels/hallo.css')]
        })

        for plugin in self.plugins:
            media += plugin.media

        return media


class HalloRichTextAreaAdapter(WidgetAdapter):
    js_constructor = 'wagtail.widgets.HalloRichTextArea'


register(HalloRichTextAreaAdapter(), HalloRichTextArea)
