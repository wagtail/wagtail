from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.telepath import Adapter, register
from wagtail.blocks.base import (
    Block,
    DeclarativeSubBlocksMetaclass,
    get_error_json_data,
    get_error_list_json_data,
    get_help_icon,
)


class TypedTableBlockValidationError(ValidationError):
    def __init__(self, cell_errors=None, non_block_errors=None):
        self.cell_errors = cell_errors
        self.non_block_errors = ErrorList(non_block_errors)
        super().__init__("Validation error in TypedTableBlock")

    def as_json_data(self):
        result = {}
        if self.non_block_errors:
            result["messages"] = get_error_list_json_data(self.non_block_errors)
        if self.cell_errors:
            result["blockErrors"] = {
                row_index: {
                    col_index: get_error_json_data(cell_error)
                    for col_index, cell_error in row_errors.items()
                }
                for row_index, row_errors in self.cell_errors.items()
            }
        return result


class TypedTable:
    template = "typed_table_block/typed_table_block.html"

    def __init__(self, columns, row_data, caption: str):
        # a list of dicts, each with items 'block' (the block instance) and 'heading'
        self.columns = columns

        # a list of dicts, each with an item 'values' (the list of block values)
        self.row_data = row_data

        self.caption = caption

    @property
    def rows(self):
        """
        Iterate over the rows of the table, with each row returned as a list of BoundBlocks
        """
        for row in self.row_data:
            yield [
                column["block"].bind(value)
                for column, value in zip(self.columns, row["values"])
            ]

    def get_context(self, parent_context=None):
        context = parent_context or {}
        context.update(
            {
                "self": self,
                "value": self,
            }
        )
        return context

    def render_as_block(self, context=None):
        return render_to_string(self.template, self.get_context(context))


class BaseTypedTableBlock(Block):
    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super().__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self.child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

    @classmethod
    def construct_from_lookup(cls, lookup, child_blocks, **kwargs):
        if child_blocks:
            child_blocks = [
                (name, lookup.get_block(index)) for name, index in child_blocks
            ]
        return cls(child_blocks, **kwargs)

    def value_from_datadict(self, data, files, prefix):
        caption = data["%s-caption" % prefix]

        column_count = int(data["%s-column-count" % prefix])
        columns = [
            {
                "id": i,
                "type": data["%s-column-%d-type" % (prefix, i)],
                "order": int(data["%s-column-%d-order" % (prefix, i)]),
                "heading": data["%s-column-%d-heading" % (prefix, i)],
            }
            for i in range(0, column_count)
            if not data["%s-column-%d-deleted" % (prefix, i)]
        ]
        columns.sort(key=lambda col: col["order"])
        for col in columns:
            col["block"] = self.child_blocks[col["type"]]

        row_count = int(data["%s-row-count" % prefix])
        rows = [
            {
                "id": row_index,
                "order": int(data["%s-row-%d-order" % (prefix, row_index)]),
                "values": [
                    col["block"].value_from_datadict(
                        data, files, "%s-cell-%d-%d" % (prefix, row_index, col["id"])
                    )
                    for col in columns
                ],
            }
            for row_index in range(0, row_count)
            if not data["%s-row-%d-deleted" % (prefix, row_index)]
        ]
        rows.sort(key=lambda row: row["order"])

        return TypedTable(
            columns=[
                {"block": col["block"], "heading": col["heading"]} for col in columns
            ],
            row_data=[{"values": row["values"]} for row in rows],
            caption=caption,
        )

    def get_prep_value(self, table):
        return {
            "columns": [
                {"type": col["block"].name, "heading": col["heading"]}
                for col in table.columns
            ],
            "rows": [
                {
                    "values": [
                        column["block"].get_prep_value(val)
                        for column, val in zip(table.columns, row["values"])
                    ]
                }
                for row in table.row_data
            ],
            "caption": table.caption,
        }

    def get_api_representation(self, table, context=None):
        return {
            "columns": [
                {"type": col["block"].name, "heading": col["heading"]}
                for col in table.columns
            ],
            "rows": [
                {
                    "values": [
                        column["block"].get_api_representation(val, context=context)
                        for column, val in zip(table.columns, row["values"])
                    ]
                }
                for row in table.row_data
            ],
            "caption": table.caption,
        }

    def normalize(self, value):
        if value is None:
            return TypedTable(
                columns=[],
                row_data=[],
                caption="",
            )
        elif isinstance(value, TypedTable):
            return value
        return self.to_python(value)

    def to_python(self, value):
        if value:
            columns = [
                {
                    "block": self.child_blocks[col["type"]],
                    "heading": col["heading"],
                }
                for col in value["columns"]
            ]
            # restore data column-by-column to take advantage of bulk_to_python
            columns_data = [
                col["block"].bulk_to_python(
                    [row["values"][column_index] for row in value["rows"]]
                )
                for column_index, col in enumerate(columns)
            ]
            return TypedTable(
                columns=columns,
                row_data=[
                    {"values": [column_data[row_index] for column_data in columns_data]}
                    for row_index in range(0, len(value["rows"]))
                ],
                caption=value.get("caption", ""),
            )
        else:
            return TypedTable(
                columns=[],
                row_data=[],
                caption="",
            )

    def get_form_state(self, table):
        return {
            "columns": [
                {"type": col["block"].name, "heading": col["heading"]}
                for col in table.columns
            ],
            "rows": [
                {
                    "values": [
                        column["block"].get_form_state(val)
                        for column, val in zip(table.columns, row["values"])
                    ]
                }
                for row in table.row_data
            ],
            "caption": table.caption,
        }

    def clean(self, table):
        cell_errors = {}
        cleaned_rows = []
        for row_index, row in enumerate(table.row_data):
            row_errors = {}
            row_data = []
            for col_index, column in enumerate(table.columns):
                val = row["values"][col_index]
                try:
                    row_data.append(column["block"].clean(val))
                except ValidationError as e:
                    row_errors[col_index] = e

            if row_errors:
                cell_errors[row_index] = row_errors
            else:
                cleaned_rows.append({"values": row_data})

        if cell_errors:
            raise TypedTableBlockValidationError(cell_errors=cell_errors)
        else:
            return TypedTable(
                columns=table.columns, row_data=cleaned_rows, caption=table.caption
            )

    def deconstruct(self):
        """
        Always deconstruct TypedTableBlock instances as if they were plain TypedTableBlock with all
        of the field definitions passed to the constructor - even if in reality this is a subclass
        with the fields defined declaratively, or some combination of the two.

        This ensures that the field definitions get frozen into migrations, rather than leaving a
        reference to a custom subclass in the user's models.py that may or may not stick around.
        """
        path = "wagtail.contrib.typed_table_block.blocks.TypedTableBlock"
        args = [list(self.child_blocks.items())]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def deconstruct_with_lookup(self, lookup):
        path = "wagtail.contrib.typed_table_block.blocks.TypedTableBlock"
        args = [
            [
                (name, lookup.add_block(block))
                for name, block in self.child_blocks.items()
            ]
        ]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    def render_basic(self, value, context=None):
        if value:
            return value.render_as_block(context)
        else:
            return ""

    def get_searchable_content(self, value):
        """extract all searchable content from the typed table block (caption, headings, cells)."""
        content = []

        if not value:
            return content

        if value.caption:
            content.append(str(value.caption))

        for col in value.columns:
            heading = col.get("heading")

            if heading:
                content.append(str(heading))

        for row in value.row_data:
            for col, cell in zip(value.columns, row["values"]):
                block = col.get("block")
                if hasattr(block, "get_searchable_content"):
                    content.extend(block.get_searchable_content(cell))
                elif cell is not None:
                    content.append(str(cell))

        return content

    class Meta:
        default = None
        icon = "table"


class TypedTableBlock(BaseTypedTableBlock, metaclass=DeclarativeSubBlocksMetaclass):
    pass


class TypedTableBlockAdapter(Adapter):
    js_constructor = "wagtail.contrib.typed_table_block.blocks.TypedTableBlock"

    def js_args(self, block):
        meta = {
            "label": block.label,
            "description": block.get_description(),
            "required": block.required,
            "icon": block.meta.icon,
            "blockDefId": block.definition_prefix,
            "isPreviewable": block.is_previewable,
            "attrs": block.meta.form_attrs or {},
            "strings": {
                "CAPTION": _("Caption"),
                "CAPTION_HELP_TEXT": _(
                    "A heading that identifies the overall topic of the table, and is useful for screen reader users."
                ),
                "ADD_COLUMN": _("Add column"),
                "ADD_ROW": _("Add row"),
                "COLUMN_HEADING": _("Column heading"),
                "INSERT_COLUMN": _("Insert column"),
                "DELETE_COLUMN": _("Delete column"),
                "INSERT_ROW": _("Insert row"),
                "DELETE_ROW": _("Delete row"),
            },
        }

        help_text = getattr(block.meta, "help_text", None)
        if help_text:
            meta["helpText"] = help_text
            meta["helpIcon"] = get_help_icon()

        return [
            block.name,
            block.child_blocks.values(),
            {
                name: child_block.get_form_state(child_block.get_default())
                for name, child_block in block.child_blocks.items()
            },
            meta,
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("typed_table_block/js/typed_table_block.js"),
            ],
            css={
                "all": [
                    versioned_static("typed_table_block/css/typed_table_block.css"),
                ]
            },
        )


register(TypedTableBlockAdapter(), TypedTableBlock)
