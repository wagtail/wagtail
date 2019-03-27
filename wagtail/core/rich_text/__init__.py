from django.db.models import Model
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
        embed_rules = features.get_embed_types()
        link_rules = features.get_link_types()
        FRONTEND_REWRITER = MultiRuleRewriter([
            LinkRewriter({linktype: handler.expand_db_attributes for linktype, handler in link_rules.items()}),
            EmbedRewriter({embedtype: handler.expand_db_attributes for embedtype, handler in embed_rules.items()})
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


class EntityHandler:
    """
    An 'entity' is a placeholder tag within the saved rich text, which needs to be rewritten
    into real HTML at the point of rendering. Typically (but not necessarily) the entity will
    be a reference to a model to be fetched to have its data output into the rich text content
    (so that we aren't storing potentially changeable data within the saved rich text).

    An EntityHandler defines how this rewriting is performed.

    Currently Wagtail supports two kinds of entity: links (represented as <a linktype="...">...</a>)
    and embeds (represented as <embed embedtype="..." />).
    """
    @staticmethod
    def get_model():
        """
        If supported, returns the type of model able to be handled by this handler, e.g. Page.
        """
        raise NotImplementedError

    @classmethod
    def get_instance(cls, attrs: dict) -> Model:
        model = cls.get_model()
        return model._default_manager.get(id=attrs['id'])

    @staticmethod
    def expand_db_attributes(attrs: dict) -> str:
        """
        Given a dict of attributes from the entity tag
        stored in the database, returns the real HTML representation.
        """
        raise NotImplementedError


class LinkHandler(EntityHandler):
    pass


class EmbedHandler(EntityHandler):
    pass
