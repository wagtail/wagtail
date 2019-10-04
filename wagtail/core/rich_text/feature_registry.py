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
        self.link_types[handler.identifier] = handler

    def get_link_types(self):
        if not self.has_scanned_for_features:
            self._scan_for_features()
        return self.link_types

    def register_embed_type(self, handler):
        self.embed_types[handler.identifier] = handler

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

    @staticmethod
    def function_as_entity_handler(identifier, fn):
        """Supports legacy registering of entity handlers as functions."""
        return type('EntityHandlerRegisteredAsFunction', (object,), {
            'identifier': identifier,
            'expand_db_attributes': staticmethod(fn),
        })
