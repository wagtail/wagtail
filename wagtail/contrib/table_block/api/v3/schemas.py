from typing import Any, Literal, NotRequired

from wagtail.api.v3.schemas.generators.blocks import BlockSchemaBuilder
from wagtail.blocks import Block


def table_block_schema(builder: BlockSchemaBuilder, block: Block, name: str) -> Any:
    def field(annotation: Any, *, required: bool = True) -> Any:
        if builder.for_input or not required:
            return NotRequired[annotation]
        return annotation

    cell = builder.get_typed_dict(
        "TableBlockCell",
        {
            "row": int,
            "col": int,
            "className": NotRequired[str],
            "hidden": NotRequired[bool],
        },
    )
    merged_cell = builder.get_typed_dict(
        "TableBlockMergedCell",
        {"row": int, "col": int, "rowspan": int, "colspan": int},
    )
    table = builder.get_typed_dict(
        type(block).__name__,
        {
            "data": field(list[list[str | None]]),
            "table_header_choice": field(Literal["row", "column", "both", "neither"]),
            "first_row_is_table_header": field(bool),
            "first_col_is_header": field(bool),
            "table_caption": field(str, required=False),
            "cell": field(list[cell], required=False),
            "mergeCells": field(list[merged_cell], required=False),
        },
    )
    return table | None
