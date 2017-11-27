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

        # a mapping of feature names to whitelister element rules that should be merged into
        # the whitelister element_rules config when the feature is active
        self.whitelister_element_rules = {}

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

    def register_whitelister_element_rules(self, feature_name, ruleset):
        self.whitelister_element_rules[feature_name] = ruleset

    def get_whitelister_element_rules(self, feature_name):
        if not self.has_scanned_for_features:
            self._scan_for_features()

        return self.whitelister_element_rules.get(feature_name, {})
