from typing import Any, Literal, NotRequired, Union, cast

from wagtail.api.v3.schemas.generators.blocks import BlockSchemaBuilder, _pascal_case
from wagtail.blocks import Block
from wagtail.contrib.typed_table_block.blocks import (
    BaseTypedTableBlock,
    TypedTableBlock,
)


def typed_table_block_schema(
    builder: BlockSchemaBuilder, block: Block, name: str
) -> Any:
    block = cast(BaseTypedTableBlock, block)
    if type(block) is not TypedTableBlock:
        name = type(block).__name__

    def field(annotation: Any) -> Any:
        return NotRequired[annotation] if builder.for_input else annotation

    if block.child_blocks:
        column_type = Literal[tuple(block.child_blocks)]
        # A cell can't be tied to its column's type, so allow any of them
        cell_type = Union[  # noqa: UP007
            tuple(
                builder.get_type(child_block, f"{name}{_pascal_case(child_name)}")
                for child_name, child_block in block.child_blocks.items()
            )
        ]
    else:
        column_type = str
        cell_type = Any

    column = builder.get_typed_dict(
        f"{name}Column", {"type": column_type, "heading": field(str)}
    )
    row = builder.get_typed_dict(f"{name}Row", {"values": field(list[cell_type])})
    return builder.get_typed_dict(
        name,
        {
            "columns": field(list[column]),
            "rows": field(list[row]),
            "caption": field(str),
        },
    )
