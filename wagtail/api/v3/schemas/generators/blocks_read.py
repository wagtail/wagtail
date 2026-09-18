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

Dispatch is via ``block_schemas``, a map of Block class -> schema function,
walked along each block's mro (like ``field_schemas`` in ``read.py`` does
for Django field classes), mirroring each container's own
``get_api_representation`` (``BaseStreamBlock``/``ListBlock``/
``BaseStructBlock``), so a project-defined subclass of one of those that
doesn't override the representation method is recursed into normally with
no special case needed. ``ImageBlock`` *does* override
``BaseStructBlock.get_api_representation`` (to convert its internal
``Image`` instance back into a plain struct dict before delegating to
``super().get_api_representation()``), but that override has been read and
confirmed to still produce the same plain-dict shape a child-by-child
StructBlock recursion would - so it gets its own registered entry that
delegates straight to the StructBlock one, taking priority over it since
mro puts ``ImageBlock`` before ``BaseStructBlock``, rather than falling
into the generic "any override means Any" rule.
"""

from decimal import Decimal
from typing import Annotated, Any, Callable, Literal, Union, cast

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

BlockSchemaFunc = Callable[["BlockSchemaBuilder", Block, str], Any]


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _overrides(block: Block, base: type[Block], method_name: str) -> bool:
    return getattr(type(block), method_name) is not getattr(base, method_name)


def _fixed_type_block_schema(
    base: type[Block], fixed_type: Any, *, check_get_prep_value: bool = True
) -> BlockSchemaFunc:
    """Build a ``block_schemas`` entry for a block with a fixed value type.

    ``base`` is the class whose ``get_api_representation`` (and, unless
    ``check_get_prep_value`` is False, ``get_prep_value``) has been read and
    confirmed to return ``fixed_type`` - a project subclass of ``base`` that
    doesn't override either method is covered too, since dispatch walks the
    block's mro looking for a registered class.
    """

    def schema(builder: "BlockSchemaBuilder", block: Block, name_prefix: str) -> Any:
        if _overrides(block, base, "get_api_representation") or (
            check_get_prep_value and _overrides(block, base, "get_prep_value")
        ):
            return Any
        return fixed_type

    return schema


def _stream_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    if _overrides(block, BaseStreamBlock, "get_api_representation"):
        return Any
    item_union = builder.build_item_union(cast(BaseStreamBlock, block), name_prefix)
    return list[item_union] if item_union is not Any else list[Any]


def _list_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    block = cast(ListBlock, block)
    if _overrides(block, ListBlock, "get_api_representation"):
        return Any
    child_type = builder._block_value_type(block.child_block, f"{name_prefix}Item")
    return list[child_type]


def _struct_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    block = cast(BaseStructBlock, block)
    struct_name = name_prefix
    namespace: dict[str, Any] = {"__annotations__": {}}
    for child_name, child_block in block.child_blocks.items():
        child_type = builder._block_value_type(
            child_block, f"{name_prefix}{_pascal_case(child_name)}"
        )
        namespace["__annotations__"][child_name] = child_type | None
        namespace[child_name] = None
    return type(Schema)(struct_name, (Schema,), namespace)


def _image_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    # ImageBlock overrides get_api_representation, but only to convert its
    # internal Image instance back to a plain struct dict before delegating
    # to the real BaseStructBlock logic - see module docstring. Any other
    # override of BaseStructBlock itself is unverified, -> Any via that entry.
    return _struct_block_schema(builder, block, name_prefix)


class BlockSchemaBuilder:
    """Builds per-StreamField item schemas for one ``streamfield_schema`` call.

    Class names are deterministic (model + field + block name), so repeated
    calls for the same field produce identically-named, identically-shaped
    classes rather than colliding.
    """

    block_schemas: dict[type[Block], BlockSchemaFunc] = {}
    """
    Map of Block classes to functions that return the type annotation for a
    block's ``value``, given the builder (for recursing into children) and a
    name prefix (for naming any generated nested Schema classes). Walked by
    mro - see ``_block_value_type``.
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

        for cls in type(block).__mro__:
            if cls in self.block_schemas:
                return self.block_schemas[cls](self, block, name_prefix)

        return Any


BlockSchemaBuilder.block_schemas[BaseStreamBlock] = _stream_block_schema
BlockSchemaBuilder.block_schemas[ListBlock] = _list_block_schema
BlockSchemaBuilder.block_schemas[ImageBlock] = _image_block_schema
BlockSchemaBuilder.block_schemas[BaseStructBlock] = _struct_block_schema
BlockSchemaBuilder.block_schemas[RichTextBlock] = _fixed_type_block_schema(
    RichTextBlock, str | None, check_get_prep_value=False
)
# get_api_representation isn't overridden on the base ChooserBlock, but
# get_prep_value is (-> the related object's pk) - a subclass that overrides
# either beyond that (e.g. ExtendedImageChooserBlock in the test app, which
# branches on the request) can't be trusted to still return a bare pk.
BlockSchemaBuilder.block_schemas[ChooserBlock] = _fixed_type_block_schema(
    ChooserBlock, int | None
)
BlockSchemaBuilder.block_schemas[StaticBlock] = _fixed_type_block_schema(
    StaticBlock, type(None), check_get_prep_value=False
)
BlockSchemaBuilder.block_schemas[MultipleChoiceBlock] = _fixed_type_block_schema(
    MultipleChoiceBlock, list[str] | None, check_get_prep_value=False
)
BlockSchemaBuilder.block_schemas[ChoiceBlock] = _fixed_type_block_schema(
    ChoiceBlock, str | None, check_get_prep_value=False
)
BlockSchemaBuilder.block_schemas[BlockQuoteBlock] = _fixed_type_block_schema(
    BlockQuoteBlock, str | None
)
BlockSchemaBuilder.block_schemas[TextBlock] = _fixed_type_block_schema(
    TextBlock, str | None
)
BlockSchemaBuilder.block_schemas[CharBlock] = _fixed_type_block_schema(
    CharBlock, str | None
)
BlockSchemaBuilder.block_schemas[RegexBlock] = _fixed_type_block_schema(
    RegexBlock, str | None
)
BlockSchemaBuilder.block_schemas[EmailBlock] = _fixed_type_block_schema(
    EmailBlock, str | None
)
BlockSchemaBuilder.block_schemas[URLBlock] = _fixed_type_block_schema(
    URLBlock, str | None
)
BlockSchemaBuilder.block_schemas[RawHTMLBlock] = _fixed_type_block_schema(
    RawHTMLBlock, str | None
)
BlockSchemaBuilder.block_schemas[BooleanBlock] = _fixed_type_block_schema(
    BooleanBlock, bool | None
)
BlockSchemaBuilder.block_schemas[IntegerBlock] = _fixed_type_block_schema(
    IntegerBlock, int | None
)
BlockSchemaBuilder.block_schemas[FloatBlock] = _fixed_type_block_schema(
    FloatBlock, float | None
)
BlockSchemaBuilder.block_schemas[DecimalBlock] = _fixed_type_block_schema(
    DecimalBlock, Decimal | None
)
BlockSchemaBuilder.block_schemas[DateBlock] = _fixed_type_block_schema(
    DateBlock, str | None
)
BlockSchemaBuilder.block_schemas[TimeBlock] = _fixed_type_block_schema(
    TimeBlock, str | None
)
BlockSchemaBuilder.block_schemas[DateTimeBlock] = _fixed_type_block_schema(
    DateTimeBlock, str | None
)


def streamfield_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field = cast(StreamField, field)
    field_name = field.name
    model = field.model
    name_prefix = f"{model._meta.object_name}{_pascal_case(field_name)}"

    builder = BlockSchemaBuilder(generator, name_prefix)
    item_union = builder.build_item_union(field.stream_block, name_prefix)
    annotation = list[item_union] if item_union is not Any else list[Any]

    def resolve(obj: Model, context: dict) -> Any:
        value = getattr(obj, field_name)
        return value.stream_block.get_api_representation(value, context)

    return cast(type, annotation), [], staticmethod(resolve)
