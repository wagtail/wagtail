import re
from functools import lru_cache
from html import unescape
from typing import List

from django.core.validators import MaxLengthValidator
from django.db.models import Model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from wagtail.rich_text.feature_registry import FeatureRegistry
from wagtail.rich_text.rewriters import EmbedRewriter, LinkRewriter, MultiRuleRewriter

features = FeatureRegistry()


# Rewriter function to be built up on first call to expand_db_html, using the utility classes
# from wagtail.rich_text.rewriters along with the embed handlers / link handlers registered
# with the feature registry


@lru_cache(maxsize=None)
def get_rewriter():
    embed_rules = features.get_embed_types()
    link_rules = features.get_link_types()
    return MultiRuleRewriter(
        [
            LinkRewriter(
                bulk_rules={
                    linktype: handler.expand_db_attributes_many
                    for linktype, handler in link_rules.items()
                },
                reference_extractors={
                    linktype: handler.extract_references
                    for linktype, handler in link_rules.items()
                },
            ),
            EmbedRewriter(
                bulk_rules={
                    embedtype: handler.expand_db_attributes_many
                    for embedtype, handler in embed_rules.items()
                },
                reference_extractors={
                    embedtype: handler.extract_references
                    for embedtype, handler in embed_rules.items()
                },
            ),
        ]
    )


def expand_db_html(html):
    """
    Expand database-representation HTML into proper HTML usable on front-end templates
    """
    rewriter = get_rewriter()
    return rewriter(html)


def extract_references_from_rich_text(html):
    rewriter = get_rewriter()
    yield from rewriter.extract_references(html)


def get_text_for_indexing(richtext):
    """
    Return a plain text version of a rich text string, suitable for search indexing;
    like Django's strip_tags, but ensures that whitespace is left between block elements
    so that <p>hello</p><p>world</p> gives "hello world", not "helloworld".
    """
    # insert space after </p>, </h1> - </h6>, </li> and </blockquote> tags
    richtext = re.sub(
        r"(</(p|h\d|li|blockquote)>)", r"\1 ", richtext, flags=re.IGNORECASE
    )
    # also insert space after <br /> and <hr />
    richtext = re.sub(r"(<(br|hr)\s*/>)", r"\1 ", richtext, flags=re.IGNORECASE)
    return unescape(strip_tags(richtext).strip())


class RichText:
    """
    A custom object used to represent a renderable rich text value.
    Provides a 'source' property to access the original source code,
    and renders to the front-end HTML rendering.
    Used as the native value of a wagtailcore.blocks.field_block.RichTextBlock.
    """

    def __init__(self, source):
        self.source = source or ""

    def __html__(self):
        return render_to_string(
            "wagtailcore/shared/richtext.html", {"html": expand_db_html(self.source)}
        )

    def __str__(self):
        return mark_safe(self.__html__())

    def __bool__(self):
        return bool(self.source)

    def __eq__(self, other):
        if isinstance(other, RichText):
            return self.source == other.source
        return False


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
        return model._default_manager.get(id=attrs["id"])

    @classmethod
    def get_many(cls, attrs_list: List[dict]) -> List[Model]:
        model = cls.get_model()
        instance_ids = [attrs.get("id") for attrs in attrs_list]
        instances_by_id = model._default_manager.in_bulk(instance_ids)
        instances_by_str_id = {str(k): v for k, v in instances_by_id.items()}
        return [instances_by_str_id.get(str(id_)) for id_ in instance_ids]

    @staticmethod
    def expand_db_attributes(attrs: dict) -> str:
        """
        Given a dict of attributes from the entity tag
        stored in the database, returns the real HTML representation.
        """
        raise NotImplementedError

    @classmethod
    def expand_db_attributes_many(cls, attrs_list: List[dict]) -> List[str]:
        """
        Given a list of attribute dicts from a list of entity tags stored in
        the database, return the real HTML representation of each one.
        """
        return list(map(cls.expand_db_attributes, attrs_list))

    @classmethod
    def extract_references(cls, attrs):
        """
        Yields a sequence of (content_type_id, object_id, model_path, content_path) tuples for the
        database objects referenced by this entity, as per
        wagtail.models.ReferenceIndex._extract_references_from_object
        """
        return []


class LinkHandler(EntityHandler):
    pass


class EmbedHandler(EntityHandler):
    pass


class RichTextMaxLengthValidator(MaxLengthValidator):
    """
    A variant of MaxLengthValidator that only counts text (not HTML tags) towards the limit
    Un-escapes entities for consistency with client-side character count.
    """

    def clean(self, x):
        return len(unescape(strip_tags(x)))
