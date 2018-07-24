from django.db.models import Model
from django.utils.html import escape

from wagtail.core import hooks


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

        # a mapping of linktype names to rewriter functions for converting database representations
        # of links (e.g. <a linktype="page" id="123">) into front-end HTML. Each rewriter function
        # takes a dict of attributes, and returns the rewritten opening tag as a string
        self.link_types = {}

        # a mapping of embedtype names to rewriter functions for converting database representations
        # of embedded content (e.g. <embed embedtype="image" id="123" format="left" alt="foo">)
        # into front-end HTML. Each rewriter function takes a dict of attributes, and returns an
        # HTML fragment to replace it with
        self.embed_types = {}

        # a dict of dicts, one for each converter backend (editorhtml, contentstate etc);
        # each dict is a mapping of feature names to 'rule' objects that define how to convert
        # that feature's elements between editor representation and database representation
        # (e.g. elements to whitelist, functions for transferring attributes).
        # The API of that rule object is not defined here, and is specific to each converter backend.
        self.converter_rules_by_converter = {}

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

    def register_link_type(self, handler):
        self.link_types[handler.link_type] = handler

    def get_link_types(self):
        if not self.has_scanned_for_features:
            self._scan_for_features()
        return self.link_types

    def register_embed_type(self, handler):
        self.embed_types[handler.link_type] = handler

    def get_embed_types(self):
        if not self.has_scanned_for_features:
            self._scan_for_features()
        return self.embed_types

    def register_converter_rule(self, converter_name, feature_name, rule):
        rules = self.converter_rules_by_converter.setdefault(converter_name, {})
        rules[feature_name] = rule

    def get_converter_rule(self, converter_name, feature_name):
        if not self.has_scanned_for_features:
            self._scan_for_features()

        try:
            return self.converter_rules_by_converter[converter_name][feature_name]
        except KeyError:
            return None


class HTMLElement(dict):
    def __init__(self, name: str, is_closing: bool = False, **attrs):
        self.name = name
        self.is_closing = is_closing
        super().__init__(**attrs)

    @property
    def open_tag(self) -> str:
        attrs = ''
        for k, v in sorted(self.items()):
            if v is not False:
                attrs += ' %s="%s"' % (escape(k.replace('_', '-')), escape(v))
        params = (self.name, attrs)
        if self.is_closing:
            return '<%s%s />' % params
        return '<%s%s>' % params

    @property
    def close_tag(self) -> str:
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

    link_type = None
    tag_name = 'a'

    @staticmethod
    def get_model():
        raise NotImplementedError

    @classmethod
    def get_instance(cls, attrs: dict) -> Model:
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
            return {'data-linktype': cls.link_type, 'data-id': instance.pk}
        return {}

    @classmethod
    def to_open_tag(cls, attrs: dict, for_editor: bool) -> str:
        """
        Given a dict of attributes from the <`tag_name`> tag
        stored in the database, returns the real HTML representation.
        """
        instance = cls.get_instance(attrs)
        tag = HTMLElement(cls.tag_name)
        if instance is not None:
            tag.update(cls.get_html_attributes(instance, for_editor))
        return tag.open_tag

    @classmethod
    def to_frontend_open_tag(cls, attrs: dict) -> str:
        return cls.to_open_tag(attrs, for_editor=False)

    @classmethod
    def to_editor_open_tag(cls, attrs: dict) -> str:
        return cls.to_open_tag(attrs, for_editor=True)
