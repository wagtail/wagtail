import json
import logging
import re

from draftjs_exporter.defaults import render_children
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML as HTMLExporter

from wagtail.admin.rich_text.converters.html_to_contentstate import HtmlToContentStateHandler
from wagtail.core.rich_text import features as feature_registry


def link_entity(props):
    """
    <a linktype="page" id="1">internal page link</a>
    """
    id_ = props.get('id')
    link_props = {}

    if id_ is not None:
        link_props['linktype'] = 'page'
        link_props['id'] = id_
    else:
        link_props['href'] = props.get('url')

    return DOM.create_element('a', link_props, props['children'])


def br(props):
    if props['block']['type'] == 'code-block':
        return props['children']

    return DOM.create_element('br')


def block_fallback(props):
    type_ = props['block']['type']
    logging.error('Missing config for "%s". Deleting block.' % type_)
    return None


def entity_fallback(props):
    type_ = props['entity']['type']
    logging.warn('Missing config for "%s". Deleting entity' % type_)
    return None


class ContentstateConverter():
    def __init__(self, features=None):
        self.features = features
        self.html_to_contentstate_handler = HtmlToContentStateHandler(features)

        exporter_config = {
            'block_map': {
                'unstyled': 'p',
                'atomic': render_children,
                'fallback': block_fallback,
            },
            'style_map': {},
            'entity_decorators': {
                'FALLBACK': entity_fallback,
            },
            'composite_decorators': [
                {
                    'strategy': re.compile(r'\n'),
                    'component': br,
                },
            ],
            'engine': DOM.STRING,
        }

        for feature in self.features:
            rule = feature_registry.get_converter_rule('contentstate', feature)
            if rule is not None:
                feature_config = rule['to_database_format']
                exporter_config['block_map'].update(feature_config.get('block_map', {}))
                exporter_config['style_map'].update(feature_config.get('style_map', {}))
                exporter_config['entity_decorators'].update(feature_config.get('entity_decorators', {}))

        self.exporter = HTMLExporter(exporter_config)

    def from_database_format(self, html):
        self.html_to_contentstate_handler.reset()
        self.html_to_contentstate_handler.feed(html)
        self.html_to_contentstate_handler.close()

        return self.html_to_contentstate_handler.contentstate.as_json(indent=4, separators=(',', ': '))

    def to_database_format(self, contentstate_json):
        return self.exporter.render(json.loads(contentstate_json))
