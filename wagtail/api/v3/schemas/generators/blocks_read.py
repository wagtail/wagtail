"""Accurate (non-advisory) read schemas for StreamField block values.

Unlike the write side (see ``blocks_write.py``), there's no tension here
between "trust the typed shape" and "fall back because input might be
malformed": every value reaching this schema has already been produced by
``Block.get_api_representation``, real Python objects this codebase itself
generated, not untrusted client input. So a block can be typed accurately
whenever we've actually read its ``get_api_representation``/``get_prep_value``
and confirmed it returns a fixed shape - no ``Any``-vs-typed union race, no
``union_mode`` fix needed.

``Any`` is still used, but only where we've decided *not* to model a block
precisely: either because its representation method is one we haven't
inspected (any block class, built-in or custom, that overrides
``get_api_representation``/``get_prep_value`` beyond the specific overrides
enumerated below), or because it's genuinely dynamic per-request (see
``ExtendedImageChooserBlock`` in the test app, which returns a different
*shape* depending on a query param - not just a different value).

The dispatch here is ``isinstance``-based, mirroring each container's own
``get_api_representation`` (``BaseStreamBlock``/``ListBlock``/
``BaseStructBlock``), so a project-defined subclass of one of those that
doesn't override the representation method is recursed into normally with
no special case needed. ``ImageBlock`` *does* override
``BaseStructBlock.get_api_representation`` (to convert its internal
``Image`` instance back into a plain struct dict before delegating to
``super().get_api_representation()``), but that override has been read and
confirmed to still produce the same plain-dict shape a child-by-child
StructBlock recursion would - so it gets an explicit pass-through special
case rather than falling into the generic "any override means Any" rule.
"""

from decimal import Decimal
from typing import Annotated, Any, Literal, Union, cast

from django.db.models import Field, Model
from ninja import Schema
from pydantic import Field as PydanticField

from wagtail.blocks.base import Block
from wagtail.blocks.field_block import (
    BlockQuoteBlock,
    BooleanBlock,
    CharBlock,
    ChoiceBlock,
    ChooserBlock,
    DateBlock,
    DateTimeBlock,
    DecimalBlock,
    EmailBlock,
    FloatBlock,
    IntegerBlock,
    MultipleChoiceBlock,
    RawHTMLBlock,
    RegexBlock,
    RichTextBlock,
    TextBlock,
    TimeBlock,
    URLBlock,
)
from wagtail.blocks.list_block import ListBlock
from wagtail.blocks.static_block import StaticBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock

from .read import FieldSchema, SchemaGenerator

#: Leaf block classes whose get_api_representation/get_prep_value we've
#: read and confirmed returns a fixed, simple type - checked by isinstance,
#: so a project subclass of one of these that doesn't override either
#: method is covered too. Order doesn't matter here (unlike the write
#: side's form-field MRO walk): these are disjoint, exact-enough classes.
_LEAF_BLOCK_TYPES: tuple[tuple[type[Block], Any], ...] = (
    (BlockQuoteBlock, str),
    (TextBlock, str),
    (CharBlock, str),
    (RegexBlock, str),
    (EmailBlock, str),
    (URLBlock, str),
    (RawHTMLBlock, str),
    (BooleanBlock, bool),
    (IntegerBlock, int),
    (FloatBlock, float),
    (DecimalBlock, Decimal),
    (DateBlock, str),
    (TimeBlock, str),
    (DateTimeBlock, str),
)


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _overrides(block: Block, base: type[Block], method_name: str) -> bool:
    return getattr(type(block), method_name) is not getattr(base, method_name)


class _BlockSchemaBuilder:
    """Builds per-StreamField item schemas for one ``streamfield_schema`` call.

    Class names are deterministic (model + field + block name), so repeated
    calls for the same field produce identically-named, identically-shaped
    classes rather than colliding.
    """

    def __init__(self, generator: SchemaGenerator, name_prefix: str):
        self.generator = generator
        self.name_prefix = name_prefix
        self._seen_block_ids: set[int] = set()

    def build_item_union(self, stream_block: BaseStreamBlock, name_prefix: str) -> Any:
        """Return a discriminated Union of per-block-type item schemas for
        ``stream_block``'s named children, or ``Any`` if it has none."""
        item_schemas = []
        for child_name, child_block in stream_block.child_blocks.items():
            item_name = f"{name_prefix}{_pascal_case(child_name)}Item"
            value_type = self._block_value_type(
                child_block, f"{name_prefix}{_pascal_case(child_name)}"
            )
            item_schema = type(Schema)(
                item_name,
                (Schema,),
                {
                    "__annotations__": {
                        "type": Literal[child_name],
                        "value": value_type,
                        "id": str | None,
                    },
                    "type": child_name,
                    "value": None,
                    "id": None,
                },
            )
            item_schemas.append(item_schema)

        if not item_schemas:
            return Any
        if len(item_schemas) == 1:
            return item_schemas[0]
        return Annotated[
            Union[tuple(item_schemas)], PydanticField(discriminator="type")
        ]

    def _block_value_type(self, block: Block, name_prefix: str) -> Any:
        if id(block) in self._seen_block_ids:
            return Any
        self._seen_block_ids = self._seen_block_ids | {id(block)}

        if isinstance(block, BaseStreamBlock):
            if _overrides(block, BaseStreamBlock, "get_api_representation"):
                return Any
            item_union = self.build_item_union(block, name_prefix)
            return list[item_union] if item_union is not Any else list[Any]

        if isinstance(block, ListBlock):
            if _overrides(block, ListBlock, "get_api_representation"):
                return Any
            child_type = self._block_value_type(block.child_block, f"{name_prefix}Item")
            return list[child_type]

        if isinstance(block, BaseStructBlock):
            # ImageBlock overrides get_api_representation, but only to
            # convert its internal Image instance back to a plain struct
            # dict before delegating to the real BaseStructBlock logic - see
            # module docstring. Any other override is unverified, -> Any.
            if not isinstance(block, ImageBlock) and _overrides(
                block, BaseStructBlock, "get_api_representation"
            ):
                return Any
            struct_name = name_prefix
            namespace: dict[str, Any] = {"__annotations__": {}}
            for child_name, child_block in block.child_blocks.items():
                child_type = self._block_value_type(
                    child_block, f"{name_prefix}{_pascal_case(child_name)}"
                )
                namespace["__annotations__"][child_name] = child_type | None
                namespace[child_name] = None
            return type(Schema)(struct_name, (Schema,), namespace)

        if isinstance(block, RichTextBlock):
            if _overrides(block, RichTextBlock, "get_api_representation"):
                return Any
            return str | None

        if isinstance(block, ChooserBlock):
            # get_api_representation isn't overridden on the base ChooserBlock,
            # but get_prep_value is (-> the related object's pk) - a subclass
            # that overrides either beyond that (e.g. ExtendedImageChooserBlock
            # in the test app, which branches on the request) can't be trusted
            # to still return a bare pk.
            if _overrides(block, ChooserBlock, "get_api_representation") or _overrides(
                block, ChooserBlock, "get_prep_value"
            ):
                return Any
            return int | None

        if isinstance(block, StaticBlock):
            if _overrides(block, StaticBlock, "get_api_representation"):
                return Any
            return type(None)

        if isinstance(block, MultipleChoiceBlock):
            if _overrides(block, MultipleChoiceBlock, "get_api_representation"):
                return Any
            return list[str] | None

        if isinstance(block, ChoiceBlock):
            if _overrides(block, ChoiceBlock, "get_api_representation"):
                return Any
            return str | None

        for leaf_cls, leaf_type in _LEAF_BLOCK_TYPES:
            if isinstance(block, leaf_cls):
                if _overrides(block, leaf_cls, "get_api_representation") or _overrides(
                    block, leaf_cls, "get_prep_value"
                ):
                    return Any
                return leaf_type | None

        return Any


def streamfield_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field = cast(StreamField, field)
    field_name = field.name
    model = field.model
    name_prefix = f"{model._meta.object_name}{_pascal_case(field_name)}"

    builder = _BlockSchemaBuilder(generator, name_prefix)
    item_union = builder.build_item_union(field.stream_block, name_prefix)
    annotation = list[item_union] if item_union is not Any else list[Any]

    def resolve(obj: Model, context: dict) -> Any:
        value = getattr(obj, field_name)
        return value.stream_block.get_api_representation(value, context)

    return cast(type, annotation), [], staticmethod(resolve)
