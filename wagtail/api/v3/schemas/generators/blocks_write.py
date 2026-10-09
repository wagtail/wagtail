"""Best-effort, advisory-only input schemas for StreamField block values.

This module produces type hints for OpenAPI/schema-discovery/codegen
consumers only. It must never cause the API to reject input it wouldn't
otherwise reject: every generated field type is unioned with a bare ``Any``
fallback, so a value that doesn't match a block's inferred shape simply
validates as plain, untyped data instead of raising. Real enforcement of
StreamField input happens later, via the block's own admin form machinery
(``build_form_data``/``flatten_block_value`` in ``wagtail.api.v3.form_data``)
- this module does not call into that code and has no effect on it.

Dispatch is via ``block_schemas``, a map of Block class -> schema function,
walked along each block's mro (like ``_FORM_FIELD_TYPE_MAP`` below does for
Django form field classes). This mirrors ``flatten_block_value``'s
isinstance order (stream -> list -> struct -> richtext -> leaf), since that
function defines what shape of JSON the write endpoint actually turns into
a bound form. Unlike that function, this one asks "what shape does this
block's *form field* accept" rather than "how do I write this value into a
MultiValueDict" - a related but distinct question with its own set of
special cases (see ``_field_block_schema`` below).
"""

from typing import Annotated, Any, Callable, Literal, Union, cast

from django import forms
from django.db.models import Field
from django.forms import Field as FormField
from ninja import Schema
from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo

from wagtail.blocks.base import Block
from wagtail.blocks.field_block import (
    BaseChoiceBlock,
    ChooserBlock,
    FieldBlock,
    MultipleChoiceBlock,
    RichTextBlock,
)
from wagtail.blocks.list_block import ListBlock
from wagtail.blocks.static_block import StaticBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock
from wagtail.compat import URLField as CompatURLField
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.fields import StreamField

from .write import InputFieldSchema, InputSchemaGenerator, RichTextInputSchema

#: Map of Django form field classes to a Python/Pydantic type, walked by
#: MRO. Only for genuinely scalar leaf blocks - a block whose value is
#: structured (TableBlock) or otherwise special (RichTextBlock, ChooserBlock,
#: StaticBlock) is dispatched by ``block_schemas`` before this map is ever
#: consulted; see `_field_block_schema`.
_FORM_FIELD_TYPE_MAP: dict[type[FormField], Any] = {
    forms.CharField: str,
    forms.RegexField: str,
    forms.EmailField: str,
    forms.FloatField: float,
    forms.DecimalField: str,
    CompatURLField: str,
    forms.URLField: str,
    forms.BooleanField: bool,
    forms.DateField: str,
    forms.TimeField: str,
    forms.DateTimeField: str,
    forms.IntegerField: int,
    forms.ChoiceField: str,
    forms.MultipleChoiceField: list[str],
}

BlockSchemaFunc = Callable[["BlockSchemaBuilder", Block, str], Any]


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _stream_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    item_union = builder.build_item_union(cast(BaseStreamBlock, block), name_prefix)
    if item_union is Any:
        return list[Any]
    return Annotated[
        Union[list[item_union], list[Any]],
        PydanticField(union_mode="left_to_right"),
    ]


def _list_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    block = cast(ListBlock, block)
    child_type = builder._block_value_type(block.child_block, f"{name_prefix}Item")
    return list[child_type]


def _struct_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    block = cast(BaseStructBlock, block)
    struct_name = f"{name_prefix}{builder.generator.name_suffix}"
    namespace: dict[str, Any] = {"__annotations__": {}}
    for child_name, child_block in block.child_blocks.items():
        child_type = builder._block_value_type(
            child_block, f"{name_prefix}{_pascal_case(child_name)}"
        )
        namespace["__annotations__"][child_name] = child_type | None
        namespace[child_name] = None
    return type(Schema)(struct_name, (Schema,), namespace)


def _rich_text_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    return str | RichTextInputSchema


def _chooser_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    return int | None


def _static_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    return type(None)


def _table_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    return Any


def _choice_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    block = cast(BaseChoiceBlock, block)
    original_choices = block._constructor_kwargs.get("choices")
    is_multi = isinstance(block, MultipleChoiceBlock)
    if isinstance(original_choices, (list, tuple)):
        values = [
            choice[0]
            for choice in original_choices
            if isinstance(choice, (list, tuple)) and len(choice) == 2
        ]
        if values:
            base = Literal[tuple(values)]
            return list[base] | None if is_multi else base | None
    return list[str] | None if is_multi else str | None


def _field_block_schema(
    builder: "BlockSchemaBuilder", block: Block, name_prefix: str
) -> Any:
    form_field = cast(FormField, cast(FieldBlock, block).field)
    for cls in type(form_field).mro():
        if cls in _FORM_FIELD_TYPE_MAP:
            return _FORM_FIELD_TYPE_MAP[cls] | None
    return Any


class BlockSchemaBuilder:
    """Builds per-StreamField item schemas for one ``streamfield_schema`` call.

    Class names are derived deterministically from the model, field, block
    names, and the generator's ``name_suffix`` (see ``streamfield_schema``),
    so two calls for the same field produce identically-named (and
    identically-shaped) classes rather than colliding under different ones.
    """

    block_schemas: dict[type[Block], BlockSchemaFunc] = {}
    """
    Map of Block classes to functions that return the type annotation for a
    block's ``value``, given the builder (for recursing into children) and a
    name prefix (for naming any generated nested Schema classes). Walked by
    mro - see ``_block_value_type``.
    """

    def __init__(self, generator: InputSchemaGenerator, name_prefix: str):
        self.generator = generator
        self.name_prefix = name_prefix
        self._seen_block_ids: set[int] = set()

    def build_item_union(self, stream_block: BaseStreamBlock, name_prefix: str) -> Any:
        """Return a discriminated Union of per-block-type item schemas for
        ``stream_block``'s named children, or ``Any`` if it has none."""
        item_schemas = []
        for child_name, child_block in stream_block.child_blocks.items():
            item_name = f"{name_prefix}{_pascal_case(child_name)}Item{self.generator.name_suffix}"
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
BlockSchemaBuilder.block_schemas[BaseStructBlock] = _struct_block_schema
BlockSchemaBuilder.block_schemas[RichTextBlock] = _rich_text_block_schema
BlockSchemaBuilder.block_schemas[ChooserBlock] = _chooser_block_schema
BlockSchemaBuilder.block_schemas[StaticBlock] = _static_block_schema
BlockSchemaBuilder.block_schemas[TableBlock] = _table_block_schema
BlockSchemaBuilder.block_schemas[BaseChoiceBlock] = _choice_block_schema
BlockSchemaBuilder.block_schemas[FieldBlock] = _field_block_schema


def streamfield_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    field = cast(StreamField, field)
    model = field.model
    name_prefix = f"{model._meta.object_name}{_pascal_case(field.name)}"

    builder = BlockSchemaBuilder(generator, name_prefix)
    item_union = builder.build_item_union(field.stream_block, name_prefix)

    if item_union is Any:
        annotation = list[Any]
    else:
        annotation = Annotated[
            Union[list[item_union], list[Any]],
            PydanticField(union_mode="left_to_right"),
        ]

    default = FieldInfo(
        default=[],
        description=(
            "Best-effort shape hints per block type, for documentation and "
            "client codegen only. Not enforced: the API accepts any value "
            "that validates against the underlying block definitions at "
            "request time, which may differ from this schema."
        ),
        json_schema_extra={"x-wagtail-schema-advisory": True},
    )
    return annotation, default
