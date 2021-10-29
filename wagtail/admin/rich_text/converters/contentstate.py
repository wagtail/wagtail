import json
import logging
import re

from draftjs_exporter.defaults import render_children
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML as HTMLExporter

from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BLOCK_KEY_NAME, HtmlToContentStateHandler)
from wagtail.core.rich_text import features as feature_registry
from wagtail.core.whitelist import check_url


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
        link_props['href'] = check_url(props.get('url'))

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
    logging.warning('Missing config for "%s". Deleting entity' % type_)
    return None


def style_fallback(props):
    type_ = props['inline_style_range']['style']
    logging.warning('Missing config for "%s". Deleting style.' % type_)
    return props['children']


def persist_key_for_block(config):
    # For any block level element config for draft js exporter, return a config that retains the
    # block key in a data attribute
    if isinstance(config, dict):
        # Wrapper elements don't retain a key - we can keep them in the config as-is
        new_config = {key: value for key, value in config.items() if key in {'wrapper', 'wrapper_props'}}
        element = config.get('element')
        element_props = config.get('props', {})
    else:
        # The config is either a simple string element name, or a function
        new_config = {}
        element_props = {}
        element = config

    def element_with_uuid(props):
        added_props = {BLOCK_KEY_NAME: props['block'].get('key')}
        try:
            # See if the element is a function - if so, we can only run it and modify its return value to include the data attribute
            elt = element(props)
            if elt is not None:
                elt.attr.update(added_props)
            return elt
        except TypeError:
            # Otherwise we can do the normal process of creating a DOM element with the right element type
            # and simply adding the data attribute to its props
            added_props.update(element_props)
            return DOM.create_element(element, added_props, props['children'])

    new_config['element'] = element_with_uuid
    return new_config


class ContentstateConverter():
    def __init__(self, features=None):
        self.features = features
        self.html_to_contentstate_handler = HtmlToContentStateHandler(features)

        exporter_config = {
            'block_map': {
                'unstyled': persist_key_for_block('p'),
                'atomic': render_children,
                'fallback': block_fallback,
            },
            'style_map': {
                'FALLBACK': style_fallback,
            },
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
                exporter_config['block_map'].update({block_type: persist_key_for_block(config) for block_type, config in feature_config.get('block_map', {}).items()})
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
