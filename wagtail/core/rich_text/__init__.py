from django.utils.safestring import mark_safe

from wagtail.core.rich_text.feature_registry import FeatureRegistry
from wagtail.core.rich_text.rewriters import EmbedRewriter, LinkRewriter, MultiRuleRewriter


features = FeatureRegistry()


# Rewriter function to be built up on first call to expand_db_html, using the utility classes
# from wagtail.core.rich_text.rewriters along with the embed handlers / link handlers registered
# with the feature registry

FRONTEND_REWRITER = None


def expand_db_html(html):
    """
    Expand database-representation HTML into proper HTML usable on front-end templates
    """
    global FRONTEND_REWRITER

    if FRONTEND_REWRITER is None:
        embed_handlers = features.get_all_embed_handler_rules()
        embed_rules = {
            handler_name: handler.expand_db_attributes
            for handler_name, handler in embed_handlers.items()
        }
        link_handlers = features.get_all_link_handler_rules()
        link_rules = {
            handler_name: handler.expand_db_attributes
            for handler_name, handler in link_handlers.items()
        }

        FRONTEND_REWRITER = MultiRuleRewriter([
            LinkRewriter(link_rules), EmbedRewriter(embed_rules)
        ])

    return FRONTEND_REWRITER(html)


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
