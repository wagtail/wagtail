from __future__ import absolute_import, unicode_literals

import json

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.forms import Media, widgets
from django.utils.module_loading import import_string

from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel
from wagtail.wagtailcore.rich_text import DbWhitelister, expand_db_html, features


class HalloRichTextArea(WidgetWithScript, widgets.Textarea):
    # this class's constructor accepts a 'features' kwarg
    accepts_features = True

    def get_panel(self):
        return RichTextFieldPanel

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', None)

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.plugins = None
        else:
            # construct a list of plugin objects, by querying the feature registry
            # and keeping the non-null responses from get_editor_plugin
            self.plugins = filter(None, [
                features.get_editor_plugin('hallo', feature_name)
                for feature_name in self.features
            ])

        super(HalloRichTextArea, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            translated_value = None
        else:
            translated_value = expand_db_html(value, for_editor=True)
        return super(HalloRichTextArea, self).render(name, translated_value, attrs)

    def render_js_init(self, id_, name, value):
        if self.options is not None and 'plugins' in self.options:
            plugin_data = self.options['plugins']
        elif self.plugins is not None:
            plugin_data = {}
            for plugin in self.plugins:
                plugin.construct_plugins_list(plugin_data)
        else:
            # no plugin list specified, so initialise without a plugins arg
            # (so that it'll pick up the globally-defined halloPlugins list instead)
            return "makeHalloRichTextEditable({0});".format(json.dumps(id_))

        return "makeHalloRichTextEditable({0}, {1});".format(
            json.dumps(id_), json.dumps(plugin_data)
        )

    def value_from_datadict(self, data, files, name):
        original_value = super(HalloRichTextArea, self).value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return DbWhitelister.clean(original_value)

    @property
    def media(self):
        return Media(js=[
            static('wagtailadmin/js/vendor/hallo.js'),
            static('wagtailadmin/js/hallo-bootstrap.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-wagtaillink.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-hr.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-requireparagraphs.js'),
        ])


class HalloPlugin(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name', None)
        self.options = kwargs.pop('options', {})

    def construct_plugins_list(self, plugins):
        if self.name is not None:
            plugins[self.name] = self.options


DEFAULT_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea'
    }
}


def get_rich_text_editor_widget(name='default', features=None):
    editor_settings = getattr(settings, 'WAGTAILADMIN_RICH_TEXT_EDITORS', DEFAULT_RICH_TEXT_EDITORS)

    editor = editor_settings[name]
    options = editor.get('OPTIONS', None)
    cls = import_string(editor['WIDGET'])

    kwargs = {}

    if options is not None:
        kwargs['options'] = options

    if getattr(cls, 'accepts_features', False):
        kwargs['features'] = features

    return cls(**kwargs)
