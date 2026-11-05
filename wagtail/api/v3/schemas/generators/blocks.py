from collections.abc import Callable, Iterable
from datetime import date, datetime, time
from decimal import Decimal
from typing import (
    Annotated,
    Any,
    Literal,
    NotRequired,
    Union,
    cast,
    get_type_hints,
)

from django.db.models import IntegerField
from pydantic import Field as PydanticField
from pydantic import TypeAdapter
from typing_extensions import TypedDict

from wagtail.blocks import (
    Block,
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
    ListBlock,
    MultipleChoiceBlock,
    RawHTMLBlock,
    RegexBlock,
    RichTextBlock,
    StaticBlock,
    StreamBlock,
    StructBlock,
    TextBlock,
    TimeBlock,
    URLBlock,
)
from wagtail.blocks.field_block import BaseChoiceBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock
from wagtail.fields import StreamField

BlockSchemaFunc = Callable[["BlockSchemaBuilder", Block, str], Any]


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


class BlockSchemaBuilder:
    """
    Builds the type of a StreamField's value from its block definitions, for
    the JSON schema only - see :class:`StreamFieldJsonSchema`.

    Each StructBlock and StreamBlock child becomes a ``TypedDict``, created once
    per distinct shape and shared by every StreamField that uses it. It's named
    after the block's class if that's a subclass (e.g. a project's
    ``PersonBlock``), otherwise after its path from the nearest such block or
    StreamField (e.g. ``BlogPageBodyQuote``).

    :param for_input: build the shape the API accepts on create/update, rather
        than the shape it returns. Its type names are suffixed with ``Input``.
    """

    def __init__(self, *, for_input: bool):
        self.for_input = for_input
        self.name_suffix = "Input" if for_input else ""

        self.representation_methods = ["to_python", "get_prep_value"]
        """
        Methods that determine a block's value shape. A block that overrides
        any of these from the class it's registered under is typed as ``Any``.
        """
        if not for_input:
            self.representation_methods.append("get_api_representation")

        self.block_schemas: dict[type[Block], BlockSchemaFunc] = {}
        """
        Map of Block classes to functions that return the type of a block's
        value, given the builder (for child blocks) and a name for any
        ``TypedDict`` it creates. Looked up along the block's MRO.
        """

        self._typed_dicts: dict[tuple, type] = {}
        self._typed_dict_names: set[str] = set()
        self._stream_types: dict[tuple[type, ...], Any] = {}
        self._adapters: dict[Any, TypeAdapter] = {}

    def register_block_schema(
        self, block_class: type[Block], func: BlockSchemaFunc
    ) -> None:
        """Register a function that returns the value type for ``block_class``."""
        self.block_schemas[block_class] = func

    def get_type(self, block: Block, name: str) -> Any:
        """Return the type of ``block``'s value, or ``Any`` if it's unknown."""
        block_class = type(block)
        for cls in block_class.__mro__:
            func = self.block_schemas.get(cls)
            if func is None:
                continue
            if any(
                getattr(block_class, method) is not getattr(cls, method)
                for method in self.representation_methods
            ):
                return self.get_api_representation_type(
                    block_class, cast(type[Block], cls)
                )
            return func(self, block, name)
        return self.get_api_representation_type(block_class, Block)

    def get_api_representation_type(
        self, block_class: type[Block], base_class: type[Block]
    ) -> Any:
        """
        Return the type of ``block_class``'s value from the return annotation
        of its ``get_api_representation``, if it overrides the one from
        ``base_class``. Otherwise, the type is unknown, so return ``Any``.
        """
        method = block_class.get_api_representation
        if self.for_input or method is base_class.get_api_representation:
            return Any
        try:
            return get_type_hints(method)["return"]
        except (KeyError, NameError, TypeError):
            # No return type, or it's only available when TYPE_CHECKING
            return Any

    def get_typed_dict(self, name: str, fields: dict[str, Any]) -> type:
        """Return a ``TypedDict`` with ``fields``, reusing an identical one."""
        key = (name, tuple(fields.items()))
        if key not in self._typed_dicts:
            unique_name = f"{name}{self.name_suffix}"
            counter = 1
            while unique_name in self._typed_dict_names:
                counter += 1
                unique_name = f"{name}{counter}{self.name_suffix}"
            self._typed_dict_names.add(unique_name)
            self._typed_dicts[key] = TypedDict(unique_name, fields)  # ty: ignore[invalid-argument-type]
        return self._typed_dicts[key]

    def get_stream_type(self, items: Iterable[type]) -> Any:
        """Return a list type of the given stream item ``TypedDict`` classes,
        discriminated by their ``type``."""
        items = tuple(items)
        if not items:
            return list[Any]
        if len(items) == 1:
            return list[items[0]]  # ty: ignore[invalid-type-form]
        if items not in self._stream_types:
            # Cached, as the FieldInfo only compares equal to itself
            self._stream_types[items] = list[
                Annotated[Union[items], PydanticField(discriminator="type")]  # noqa: UP007
            ]
        return self._stream_types[items]

    def get_stream_field_adapter(self, field: StreamField) -> TypeAdapter:
        name = f"{field.model._meta.object_name}{_pascal_case(field.name)}"
        value_type = self.get_type(field.stream_block, name)
        if value_type not in self._adapters:
            self._adapters[value_type] = TypeAdapter(value_type)
        return self._adapters[value_type]


class StreamFieldJsonSchema:
    """
    Metadata for a StreamField's ``Annotated[list[Any], ...]`` schema field,
    which documents its value's shape in the JSON schema.

    The value itself isn't validated or serialized against that shape: the
    API returns whatever ``get_api_representation`` gives, and input is
    validated by the blocks themselves. So the shape is only built when the
    JSON schema is first generated, and can't reject a value it got wrong.
    """

    def __init__(self, builder: BlockSchemaBuilder, field: StreamField):
        self.builder = builder
        self.field = field
        self._adapter: TypeAdapter | None = None

    def __get_pydantic_json_schema__(self, core_schema, handler):
        if self._adapter is None:
            self._adapter = self.builder.get_stream_field_adapter(self.field)
        return handler(self._adapter.core_schema)


def _get_name(block: Block, name: str) -> str:
    if type(block) in (StreamBlock, StructBlock):
        return name
    return type(block).__name__


def stream_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    block = cast(BaseStreamBlock, block)
    name = _get_name(block, name)
    items = []
    for child_name, child_block in block.child_blocks.items():
        child_path = f"{name}{_pascal_case(child_name)}"
        items.append(
            builder.get_typed_dict(
                f"{child_path}Item",
                {
                    "type": Literal[child_name],  # ty: ignore[invalid-type-form]
                    "value": builder.get_type(child_block, child_path),
                    "id": NotRequired[str | None] if builder.for_input else str | None,
                },
            )
        )
    return builder.get_stream_type(items)


def struct_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    block = cast(BaseStructBlock, block)
    name = _get_name(block, name)
    fields = {}
    for child_name, child_block in block.child_blocks.items():
        child_type = builder.get_type(child_block, f"{name}{_pascal_case(child_name)}")
        fields[child_name] = (
            NotRequired[child_type] if builder.for_input else child_type
        )
    return builder.get_typed_dict(name, fields)


def list_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    child_block = cast(ListBlock, block).child_block
    child_type = builder.get_type(child_block, f"{name}Item")
    if builder.for_input:
        block_item = builder.get_typed_dict(
            f"{name}BlockItem",
            {"type": Literal["item"], "value": child_type, "id": str | None},
        )
        child_type = child_type | block_item
    return list[child_type]


def _choice_values(choices: Iterable) -> Iterable:
    for value, label in choices:
        if isinstance(label, (list, tuple)):
            # Optgroup
            yield from (subvalue for subvalue, _ in label)
        else:
            yield value


def choice_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    # Not block.field.choices, which would evaluate callable choices
    choices = cast(BaseChoiceBlock, block)._constructor_kwargs["choices"]
    values = () if callable(choices) else tuple(_choice_values(choices))
    if values and all(isinstance(value, (str, int)) for value in values):
        value_type = Literal[values]  # ty: ignore[invalid-type-form]
    else:
        value_type = str
    if isinstance(block, MultipleChoiceBlock):
        return list[value_type] | None
    return value_type | None


def chooser_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    # The value is the chosen object's pk
    pk_field = cast(ChooserBlock, block).pk_field
    while pk_field.is_relation:
        pk_field = pk_field.target_field
    return (int if isinstance(pk_field, IntegerField) else str) | None


def fixed_schema(value_type: Any) -> BlockSchemaFunc:
    return lambda builder, block, name: value_type


def register_default_block_schemas(builder: BlockSchemaBuilder) -> None:
    builder.register_block_schema(BaseStreamBlock, stream_block_schema)
    builder.register_block_schema(BaseStructBlock, struct_block_schema)
    builder.register_block_schema(ListBlock, list_block_schema)
    builder.register_block_schema(ChoiceBlock, choice_block_schema)
    builder.register_block_schema(MultipleChoiceBlock, choice_block_schema)
    builder.register_block_schema(ChooserBlock, chooser_block_schema)
    builder.register_block_schema(StaticBlock, fixed_schema(None))
    for block_class, value_type in [
        (CharBlock, str),
        (TextBlock, str),
        (RegexBlock, str),
        (URLBlock, str),
        (EmailBlock, str),
        (RawHTMLBlock, str),
        (RichTextBlock, str),
        (IntegerBlock, int),
        (FloatBlock, float),
        (DecimalBlock, Decimal),
        (BooleanBlock, bool),
        (DateBlock, date),
        (TimeBlock, time),
        (DateTimeBlock, datetime),
    ]:
        builder.register_block_schema(block_class, fixed_schema(value_type | None))
