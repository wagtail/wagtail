import re  # parsing HTML with regexes LIKE A BOSS.

from django.db.models import Model
from django.utils.html import escape
from django.utils.safestring import mark_safe

from wagtail.core import hooks
from wagtail.core.models import Page
from wagtail.core.whitelist import Whitelister


# Define a set of 'embed handlers' and 'link handlers'. These handle the translation
# of 'special' HTML elements in rich text - ones which we do not want to include
# verbatim in the DB representation because they embed information which is stored
# elsewhere in the database and is liable to change - from real HTML representation
# to DB representation and back again.


class HTMLElement(dict):
    def __init__(self, name: str, is_closing: bool = False, **attrs):
        self.name = name
        self.is_closing = is_closing
        super().__init__(**attrs)

    @property
    def open_tag(self):
        attrs = ''
        for k, v in sorted(self.items()):
            if v is not False:
                attrs += ' %s="%s"' % (escape(k.replace('_', '-')), escape(v))
        params = (self.name, attrs)
        if self.is_closing:
            return '<%s%s />' % params
        return '<%s%s>' % params

    @property
    def close_tag(self):
        if self.is_closing:
            return ''
        return '</%s>' % self.name


class LinkHandler:
    """
    PageLinkHandler will be invoked whenever we encounter an HTML element
    in rich text content with an attribute of data-linktype="`linktype`".
    The resulting element in the database representation will be for example:
    <a linktype="page" id="42">hello world</a>
    """

    name = None
    tag_name = 'a'

    @staticmethod
    def get_model():
        raise NotImplementedError

    @classmethod
    def get_instance(cls, attrs):
        model = cls.get_model()
        try:
            return model._default_manager.get(id=attrs['id'])
        except model.DoesNotExist:
            pass

    @staticmethod
    def get_id_pair_from_instance(instance: Model):
        return 'id', instance.pk

    @staticmethod
    def get_db_attributes(tag: dict) -> dict:
        """
        Given an <`tag_name`> tag that we've identified as a `linktype` embed
        (because it has a data-linktype="`linktype`" attribute),
        returns a dict of the attributes we should have on the resulting
        <`tag_name` linktype="`linktype`"> element.
        """
        return {'id': tag['data-id']}

    @classmethod
    def get_html_attributes(cls, instance: Model, for_editor: bool) -> dict:
        if for_editor:
            return {'data-linktype': cls.name, 'data-id': instance.pk}
        return {}

    @classmethod
    def expand_db_attributes(cls, attrs: dict, for_editor: bool) -> str:
        """
        Given a dict of attributes from the <`tag_name`> tag
        stored in the database, returns the real HTML representation.
        """
        instance = cls.get_instance(attrs)
        tag = HTMLElement(cls.tag_name)
        if instance is not None:
            tag.update(cls.get_html_attributes(instance, for_editor))
        return tag.open_tag


class PageLinkHandler(LinkHandler):
    name = 'page'

    @staticmethod
    def get_model():
        return Page

    @classmethod
    def get_instance(cls, attrs):
        page = super().get_instance(attrs)
        if page is None:
            return
        return page.specific

    @classmethod
    def get_html_attributes(cls, instance, for_editor):
        attrs = super().get_html_attributes(instance, for_editor)
        attrs['href'] = instance.specific.url
        if for_editor:
            parent_page = instance.get_parent()
            if parent_page:
                attrs['data-parent-id'] = parent_page.id
        return attrs


EMBED_HANDLERS = {}
LINK_HANDLERS = {}


@hooks.register('register_rich_text_link_handler')
def register_page_embed_handler():
    return PageLinkHandler


def register_rich_text_handlers():
    def get_handler(hook):
        # This try/except allows support for the (undocumented) old way
        # these rich text hooks worked, by returning a tuple.
        try:
            handler_name, handler = hook()
        except (TypeError, ValueError):
            handler = hook()
            handler_name = handler.name
        return handler_name, handler

    for hook in hooks.get_hooks('register_rich_text_embed_handler'):
        handler_name, handler = get_handler(hook)
        EMBED_HANDLERS[handler_name] = handler
    for hook in hooks.get_hooks('register_rich_text_link_handler'):
        handler_name, handler = get_handler(hook)
        LINK_HANDLERS[handler_name] = handler


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
    has_loaded_custom_whitelist_rules = False

    @classmethod
    def clean(cls, html):
        if not cls.has_loaded_custom_whitelist_rules:
            for fn in hooks.get_hooks('construct_whitelister_element_rules'):
                cls.element_rules = cls.element_rules.copy()
                cls.element_rules.update(fn())
            cls.has_loaded_custom_whitelist_rules = True

        return super(DbWhitelister, cls).clean(html)

    @classmethod
    def clean_tag_node(cls, doc, tag):
        if 'data-embedtype' in tag.attrs:
            embed_type = tag['data-embedtype']
            # fetch the appropriate embed handler for this embedtype
            embed_handler = EMBED_HANDLERS[embed_type]
            embed_attrs = embed_handler.get_db_attributes(tag)
            embed_attrs['embedtype'] = embed_type

            embed_tag = doc.new_tag('embed', **embed_attrs)
            embed_tag.can_be_empty_element = True
            tag.replace_with(embed_tag)
        elif tag.name == 'a' and 'data-linktype' in tag.attrs:
            # first, whitelist the contents of this tag
            for child in tag.contents:
                cls.clean_node(doc, child)

            link_type = tag['data-linktype']
            link_handler = LINK_HANDLERS[link_type]
            link_attrs = link_handler.get_db_attributes(tag)
            link_attrs['linktype'] = link_type
            tag.attrs.clear()
            tag.attrs.update(**link_attrs)
        else:
            if tag.name == 'div':
                tag.name = 'p'

            super(DbWhitelister, cls).clean_tag_node(doc, tag)


FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes as a dict. Does not escape HTML entities!
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
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
        handler = LINK_HANDLERS[attrs['linktype']]
        return handler.expand_db_attributes(attrs, for_editor)

    def replace_embed_tag(m):
        attrs = extract_attrs(m.group(1))
        handler = EMBED_HANDLERS[attrs['embedtype']]
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


class FeatureRegistry:
    """
    A central store of information about optional features that can be enabled in rich text
    editors by passing a ``features`` list to the RichTextField, such as how to
    whitelist / convert HTML tags, and how to enable the feature on various editors.

    This information may come from diverse sources - for example, wagtailimages might define
    an 'images' feature and a hallo.js plugin for it, while a third-party module might
    define a TinyMCE plugin for the same feature. The information is therefore collected into
    this registry via the 'register_rich_text_features' hook.
    """
    def __init__(self):
        # Has the register_rich_text_features hook been run for this registry?
        self.has_scanned_for_features = False

        # a dict of dicts, one for each editor (hallo.js, TinyMCE etc); each dict is a mapping
        # of feature names to 'plugin' objects that define how to implement that feature
        # (e.g. paths to JS files to import). The API of that plugin object is not defined
        # here, and is specific to each editor.
        self.plugins_by_editor = {}

        # a list of feature names that will be applied on rich text areas that do not specify
        # an explicit `feature` list.
        self.default_features = []

    def get_default_features(self):
        if not self.has_scanned_for_features:
            self._scan_for_features()

        return self.default_features

    def _scan_for_features(self):
        for fn in hooks.get_hooks('register_rich_text_features'):
            fn(self)
        self.has_scanned_for_features = True

    def register_editor_plugin(self, editor_name, feature_name, plugin):
        plugins = self.plugins_by_editor.setdefault(editor_name, {})
        plugins[feature_name] = plugin

    def get_editor_plugin(self, editor_name, feature_name):
        if not self.has_scanned_for_features:
            self._scan_for_features()

        try:
            return self.plugins_by_editor[editor_name][feature_name]
        except KeyError:
            return None


features = FeatureRegistry()
