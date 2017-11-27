import re  # parsing HTML with regexes LIKE A BOSS.

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from wagtail.core import hooks
from wagtail.core.rich_text.feature_registry import FeatureRegistry
from wagtail.core.rich_text.pages import PageLinkHandler
from wagtail.core.whitelist import allow_without_attributes, Whitelister, DEFAULT_ELEMENT_RULES


features = FeatureRegistry()


# Define a set of 'embed handlers' and 'link handlers'. These handle the translation
# of 'special' HTML elements in rich text - ones which we do not want to include
# verbatim in the DB representation because they embed information which is stored
# elsewhere in the database and is liable to change - from real HTML representation
# to DB representation and back again.


EMBED_HANDLERS = {}
LINK_HANDLERS = {
    'page': PageLinkHandler,
}

has_loaded_embed_handlers = False
has_loaded_link_handlers = False


def get_embed_handler(embed_type):
    global EMBED_HANDLERS, has_loaded_embed_handlers

    if not has_loaded_embed_handlers:
        for hook in hooks.get_hooks('register_rich_text_embed_handler'):
            handler_name, handler = hook()
            EMBED_HANDLERS[handler_name] = handler

        has_loaded_embed_handlers = True

    return EMBED_HANDLERS[embed_type]


def get_link_handler(link_type):
    global LINK_HANDLERS, has_loaded_link_handlers

    if not has_loaded_link_handlers:
        for hook in hooks.get_hooks('register_rich_text_link_handler'):
            handler_name, handler = hook()
            LINK_HANDLERS[handler_name] = handler

        has_loaded_link_handlers = True

    return LINK_HANDLERS[link_type]


class DbWhitelister(Whitelister):
    """
    A custom whitelisting engine to convert the HTML as returned by the rich text editor
    into the pseudo-HTML format stored in the database (in which images, documents and other
    linked objects are identified by ID rather than URL):

    * implements a 'construct_whitelister_element_rules' hook so that other apps can modify
      the whitelist ruleset (e.g. to permit additional HTML elements beyond those in the base
      Whitelister module);
    * replaces any element with a 'data-embedtype' attribute with an <embed> element, with
      attributes supplied by the handler for that type as defined in EMBED_HANDLERS;
    * rewrites the attributes of any <a> element with a 'data-linktype' attribute, as
      determined by the handler for that type defined in LINK_HANDLERS, while keeping the
      element content intact.
    """
    def __init__(self, features=None):
        self.features = features

    @cached_property
    def element_rules(self):
        if self.features is None:
            # use the legacy construct_whitelister_element_rules hook to build up whitelist rules
            element_rules = DEFAULT_ELEMENT_RULES.copy()
            for fn in hooks.get_hooks('construct_whitelister_element_rules'):
                element_rules.update(fn())
        else:
            # use the feature registry to build up whitelist rules
            element_rules = {
                '[document]': allow_without_attributes,
                'p': allow_without_attributes,
                'div': allow_without_attributes,
                'br': allow_without_attributes,
            }
            for feature_name in self.features:
                element_rules.update(features.get_whitelister_element_rules(feature_name))

        return element_rules

    @cached_property
    def embed_handlers(self):
        embed_handlers = {}
        for hook in hooks.get_hooks('register_rich_text_embed_handler'):
            handler_name, handler = hook()
            embed_handlers[handler_name] = handler

        return embed_handlers

    @cached_property
    def link_handlers(self):
        link_handlers = {
            'page': PageLinkHandler,
        }
        for hook in hooks.get_hooks('register_rich_text_link_handler'):
            handler_name, handler = hook()
            link_handlers[handler_name] = handler

        return link_handlers

    def clean_tag_node(self, doc, tag):
        if 'data-embedtype' in tag.attrs:
            embed_type = tag['data-embedtype']
            # fetch the appropriate embed handler for this embedtype
            embed_handler = self.embed_handlers[embed_type]
            embed_attrs = embed_handler.get_db_attributes(tag)
            embed_attrs['embedtype'] = embed_type

            embed_tag = doc.new_tag('embed', **embed_attrs)
            embed_tag.can_be_empty_element = True
            tag.replace_with(embed_tag)
        elif tag.name == 'a' and 'data-linktype' in tag.attrs:
            # first, whitelist the contents of this tag
            for child in tag.contents:
                self.clean_node(doc, child)

            link_type = tag['data-linktype']
            link_handler = self.link_handlers[link_type]
            link_attrs = link_handler.get_db_attributes(tag)
            link_attrs['linktype'] = link_type
            tag.attrs.clear()
            tag.attrs.update(**link_attrs)
        else:
            if tag.name == 'div':
                tag.name = 'p'

            super(DbWhitelister, self).clean_tag_node(doc, tag)


FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes, as a dict of un-escaped strings
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        val = val.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
        attributes[name] = val
    return attributes


def expand_db_html(html, for_editor=False):
    """
    Expand database-representation HTML into proper HTML usable in either
    templates or the rich text editor
    """
    def replace_a_tag(m):
        attrs = extract_attrs(m.group(1))
        if 'linktype' not in attrs:
            # return unchanged
            return m.group(0)
        handler = get_link_handler(attrs['linktype'])
        return handler.expand_db_attributes(attrs, for_editor)

    def replace_embed_tag(m):
        attrs = extract_attrs(m.group(1))
        handler = get_embed_handler(attrs['embedtype'])
        return handler.expand_db_attributes(attrs, for_editor)

    html = FIND_A_TAG.sub(replace_a_tag, html)
    html = FIND_EMBED_TAG.sub(replace_embed_tag, html)
    return html


class RichText:
    """
    A custom object used to represent a renderable rich text value.
    Provides a 'source' property to access the original source code,
    and renders to the front-end HTML rendering.
    Used as the native value of a wagtailcore.blocks.field_block.RichTextBlock.
    """
    def __init__(self, source):
        self.source = (source or '')

    def __html__(self):
        return '<div class="rich-text">' + expand_db_html(self.source) + '</div>'

    def __str__(self):
        return mark_safe(self.__html__())

    def __bool__(self):
        return bool(self.source)
    __nonzero__ = __bool__
