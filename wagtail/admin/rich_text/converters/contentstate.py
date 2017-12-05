import json
import logging
import re

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.defaults import render_children
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML as HTMLExporter

from wagtail.admin.rich_text.converters.html_to_contentstate import HtmlToContentStateHandler


def Image(props):
    """
    <embed alt="Right-aligned image" embedtype="image" format="right" id="1"/>
    """
    return DOM.create_element('embed', {
        'embedtype': 'image',
        'format': props.get('alignment'),
        'id': props.get('id'),
        'alt': props.get('altText'),
    })


def Embed(props):
    """
    <embed embedtype="media" url="https://www.youtube.com/watch?v=y8Kyi0WNg40"/>
    """
    return DOM.create_element('embed', {
        'embedtype': 'media',
        'url': props.get('url'),
    })


def Document(props):
    """
    <a id="1" linktype="document">document link</a>
    """

    return DOM.create_element('a', {
        'linktype': 'document',
        'id': props.get('id'),
    }, props['children'])


def Link(props):
    """
    <a linktype="page" id="1">internal page link</a>
    """
    link_type = props.get('linkType', '')
    link_props = {}

    if link_type == 'page':
        link_props['linktype'] = link_type
        link_props['id'] = props.get('id')
    else:
        link_props['href'] = props.get('url')

    return DOM.create_element('a', link_props, props['children'])


class BR:
    """
    Replace line breaks (\n) with br tags.
    """
    SEARCH_RE = re.compile(r'\n')

    def render(self, props):
        # Do not process matches inside code blocks.
        if props['block']['type'] == BLOCK_TYPES.CODE:
            return props['children']

        return DOM.create_element('br')


def BlockFallback(props):
    type_ = props['block']['type']
    logging.error('Missing config for "%s". Deleting block.' % type_)
    return None


def EntityFallback(props):
    type_ = props['entity']['type']
    logging.warn('Missing config for "%s". Deleting entity' % type_)
    return None


EXPORTER_CONFIG_BY_FEATURE = {
    'h1': {
        'block_map': {BLOCK_TYPES.HEADER_ONE: 'h1'}
    },
    'h2': {
        'block_map': {BLOCK_TYPES.HEADER_TWO: 'h2'}
    },
    'h3': {
        'block_map': {BLOCK_TYPES.HEADER_THREE: 'h3'}
    },
    'h4': {
        'block_map': {BLOCK_TYPES.HEADER_FOUR: 'h4'}
    },
    'h5': {
        'block_map': {BLOCK_TYPES.HEADER_FIVE: 'h5'}
    },
    'h6': {
        'block_map': {BLOCK_TYPES.HEADER_SIX: 'h6'}
    },
    'bold': {
        'style_map': {INLINE_STYLES.BOLD: 'b'}
    },
    'italic': {
        'style_map': {INLINE_STYLES.ITALIC: 'i'}
    },
    'ol': {
        'block_map': {BLOCK_TYPES.ORDERED_LIST_ITEM: {'element': 'li', 'wrapper': 'ol'}}
    },
    'ul': {
        'block_map': {BLOCK_TYPES.UNORDERED_LIST_ITEM: {'element': 'li', 'wrapper': 'ul'}}
    },
    'hr': {
        'entity_decorators': {ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element('hr')}
    },
    'link': {
        'entity_decorators': {ENTITY_TYPES.LINK: Link}
    },
    'document-link': {
        'entity_decorators': {ENTITY_TYPES.DOCUMENT: Document}
    },
    'image': {
        'entity_decorators': {ENTITY_TYPES.IMAGE: Image}
    },
    'embed': {
        'entity_decorators': {ENTITY_TYPES.EMBED: Embed}
    },
}


class ContentstateConverter():
    def __init__(self, features=None):
        self.features = features
        self.html_to_contentstate_handler = HtmlToContentStateHandler(features)

        exporter_config = {
            'block_map': {
                BLOCK_TYPES.UNSTYLED: 'p',
                BLOCK_TYPES.ATOMIC: render_children,
                BLOCK_TYPES.FALLBACK: BlockFallback,
            },
            'style_map': {},
            'entity_decorators': {
                ENTITY_TYPES.FALLBACK: EntityFallback,
            },
            'composite_decorators': [
                BR,
            ],
            'engine': 'html5lib',
        }

        for feature in self.features:
            feature_config = EXPORTER_CONFIG_BY_FEATURE.get(feature, {})
            exporter_config['block_map'].update(feature_config.get('block_map', {}))
            exporter_config['style_map'].update(feature_config.get('style_map', {}))
            exporter_config['entity_decorators'].update(feature_config.get('entity_decorators', {}))

        self.exporter = HTMLExporter(exporter_config)

    def from_database_format(self, html):
        self.html_to_contentstate_handler.reset()
        self.html_to_contentstate_handler.feed(html)
        return self.html_to_contentstate_handler.contentstate.as_json(indent=4, separators=(',', ': '))

    def to_database_format(self, contentstate_json):
        return self.exporter.render(json.loads(contentstate_json))
