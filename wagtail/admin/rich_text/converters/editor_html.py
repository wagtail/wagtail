import warnings

from django.utils.functional import cached_property

from wagtail.core import hooks
from wagtail.core.rich_text import features as feature_registry
from wagtail.core.rich_text.rewriters import EmbedRewriter, LinkRewriter, MultiRuleRewriter
from wagtail.core.whitelist import allow_without_attributes, Whitelister
from wagtail.utils.deprecation import RemovedInWagtail22Warning


class WhitelistRule:
    def __init__(self, element, handler):
        self.element = element
        self.handler = handler


# Whitelist rules which are always active regardless of the rich text features that are enabled

BASE_WHITELIST_RULES = {
    '[document]': allow_without_attributes,
    'p': allow_without_attributes,
    'div': allow_without_attributes,
    'br': allow_without_attributes,
}


class DbWhitelister(Whitelister):
    """
    A custom whitelisting engine to convert the HTML as returned by the rich text editor
    into the pseudo-HTML format stored in the database (in which images, documents and other
    linked objects are identified by ID rather than URL):

    * implements a 'construct_whitelister_element_rules' hook so that other apps can modify
      the whitelist ruleset (e.g. to permit additional HTML elements beyond those in the base
      Whitelister module);
    * replaces any element with a 'data-embedtype' attribute with an <embed> element, with
      attributes supplied by the handler for that type as defined in embed_handlers;
    * rewrites the attributes of any <a> element with a 'data-linktype' attribute, as
      determined by the handler for that type defined in link_handlers, while keeping the
      element content intact.
    """
    def __init__(self, converter_rules, features):
        self.element_rules = BASE_WHITELIST_RULES.copy()
        for rule in converter_rules:
            if isinstance(rule, WhitelistRule):
                self.element_rules[rule.element] = rule.handler

        # apply legacy construct_whitelister_element_rules hooks to the assembled list
        construct_whitelist_hooks = hooks.get_hooks('construct_whitelister_element_rules')
        if construct_whitelist_hooks:
            warnings.warn(
                'The construct_whitelister_element_rules hook is deprecated and will be removed '
                'in Wagtail 2.2. Use register_rich_text_features instead',
                RemovedInWagtail22Warning
            )

            for fn in construct_whitelist_hooks:
                self.element_rules.update(fn())

        self.features = features

    @cached_property
    def embed_handlers(self):
        embed_handlers = {}
        for feature in self.features:
            embed_handlers.update(feature_registry.get_embed_handler_rules(feature))

        return embed_handlers

    @cached_property
    def link_handlers(self):
        link_handlers = {}
        for feature in self.features:
            link_handlers.update(feature_registry.get_link_handler_rules(feature))

        return link_handlers

    def clean_tag_node(self, doc, tag):
        if 'data-embedtype' in tag.attrs:
            embed_type = tag['data-embedtype']
            # fetch the appropriate embed handler for this embedtype
            try:
                embed_handler = self.embed_handlers[embed_type]
            except KeyError:
                # discard embeds with unrecognised embedtypes
                tag.decompose()
                return

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
            try:
                link_handler = self.link_handlers[link_type]
            except KeyError:
                # discard links with unrecognised linktypes
                tag.unwrap()
                return

            link_attrs = link_handler.get_db_attributes(tag)
            link_attrs['linktype'] = link_type
            tag.attrs.clear()
            tag.attrs.update(**link_attrs)
        else:
            if tag.name == 'div':
                tag.name = 'p'

            super(DbWhitelister, self).clean_tag_node(doc, tag)


class EditorHTMLConverter:
    def __init__(self, features=None):
        if features is None:
            self.features = feature_registry.get_default_features()
        else:
            self.features = features

        self.converter_rules = []
        for feature in self.features:
            rule = feature_registry.get_converter_rule('editorhtml', feature)
            if rule is not None:
                # rule should be a list of WhitelistRule() instances - append this to
                # the master converter_rules list
                self.converter_rules.extend(rule)

    @cached_property
    def whitelister(self):
        return DbWhitelister(self.converter_rules, self.features)

    def to_database_format(self, html):
        return self.whitelister.clean(html)

    @cached_property
    def html_rewriter(self):
        embed_rules = {}
        link_rules = {}
        for feature in self.features:
            embed_handlers = feature_registry.get_embed_handler_rules(feature)
            for handler_name, handler in embed_handlers.items():
                embed_rules[handler_name] = handler.expand_db_attributes

            link_handlers = feature_registry.get_link_handler_rules(feature)
            for handler_name, handler in link_handlers.items():
                link_rules[handler_name] = handler.expand_db_attributes

        return MultiRuleRewriter([
            LinkRewriter(link_rules), EmbedRewriter(embed_rules)
        ])

    def from_database_format(self, html):
        return self.html_rewriter(html)
