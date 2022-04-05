import json

from django import forms
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.blocks import FieldBlock
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter

DEFAULT_TABLE_OPTIONS = {
    "minSpareRows": 0,
    "startRows": 3,
    "startCols": 3,
    "colHeaders": False,
    "rowHeaders": False,
    "contextMenu": [
        "row_above",
        "row_below",
        "---------",
        "col_left",
        "col_right",
        "---------",
        "remove_row",
        "remove_col",
        "---------",
        "undo",
        "redo",
    ],
    "editor": "text",
    "stretchH": "all",
    "height": 108,
    "renderer": "text",
    "autoColumnSize": False,
}


class TableInput(forms.HiddenInput):
    def __init__(self, table_options=None, attrs=None):
        self.table_options = table_options
        super().__init__(attrs=attrs)

    @cached_property
    def media(self):
        return forms.Media(
            css={
                "all": [
                    versioned_static(
                        "table_block/css/vendor/handsontable-6.2.2.full.min.css"
                    ),
                ]
            },
            js=[
                versioned_static(
                    "table_block/js/vendor/handsontable-6.2.2.full.min.js"
                ),
                versioned_static("table_block/js/table.js"),
            ],
        )


class TableInputAdapter(WidgetAdapter):
    js_constructor = "wagtail.widgets.TableInput"

    def js_args(self, widget):
        strings = {
            "Row header": _("Row header"),
            "Display the first row as a header.": _(
                "Display the first row as a header."
            ),
            "Column header": _("Column header"),
            "Display the first column as a header.": _(
                "Display the first column as a header."
            ),
            "Table caption": _("Table caption"),
            "A heading that identifies the overall topic of the table, and is useful for screen reader users": _(
                "A heading that identifies the overall topic of the table, and is useful for screen reader users"
            ),
            "Table": _("Table"),
        }

        return [
            widget.table_options,
            strings,
        ]


register(TableInputAdapter(), TableInput)


class TableBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, table_options=None, **kwargs):
        """
        CharField's 'label' and 'initial' parameters are not exposed, as Block
        handles that functionality natively (via 'label' and 'default')

        CharField's 'max_length' and 'min_length' parameters are not exposed as table
        data needs to have arbitrary length
        """
        self.table_options = self.get_table_options(table_options=table_options)
        self.field_options = {"required": required, "help_text": help_text}

        super().__init__(**kwargs)

    @cached_property
    def field(self):
        return forms.CharField(
            widget=TableInput(table_options=self.table_options), **self.field_options
        )

    def value_from_form(self, value):
        return json.loads(value)

    def value_for_form(self, value):
        return json.dumps(value)

    def get_form_state(self, value):
        # pass state to frontend as a JSON-ish dict - do not serialise to a JSON string
        return value

    def is_html_renderer(self):
        return self.table_options["renderer"] == "html"

    def get_searchable_content(self, value):
        content = []
        if value:
            for row in value.get("data", []):
                content.extend([v for v in row if v])
        return content

    def render(self, value, context=None):
        template = getattr(self.meta, "template", None)
        if template and value:
            table_header = (
                value["data"][0]
                if value.get("data", None)
                and len(value["data"]) > 0
                and value.get("first_row_is_table_header", False)
                else None
            )
            first_col_is_header = value.get("first_col_is_header", False)

            if context is None:
                new_context = {}
            else:
                new_context = dict(context)

            new_context.update(
                {
                    "self": value,
                    self.TEMPLATE_VAR: value,
                    "table_header": table_header,
                    "first_col_is_header": first_col_is_header,
                    "html_renderer": self.is_html_renderer(),
                    "table_caption": value.get("table_caption"),
                    "data": value["data"][1:]
                    if table_header
                    else value.get("data", []),
                }
            )

            if value.get("cell"):
                new_context["classnames"] = {}
                new_context["hidden"] = {}
                for meta in value["cell"]:
                    if "className" in meta:
                        new_context["classnames"][(meta["row"], meta["col"])] = meta[
                            "className"
                        ]
                    if "hidden" in meta:
                        new_context["hidden"][(meta["row"], meta["col"])] = meta[
                            "hidden"
                        ]

            if value.get("mergeCells"):
                new_context["spans"] = {}
                for merge in value["mergeCells"]:
                    new_context["spans"][(merge["row"], merge["col"])] = {
                        "rowspan": merge["rowspan"],
                        "colspan": merge["colspan"],
                    }

            return render_to_string(template, new_context)
        else:
            return self.render_basic(value or "", context=context)

    def get_table_options(self, table_options=None):
        """
        Return a dict of table options using the defaults unless custom options provided

        table_options can contain any valid handsontable options:
        https://handsontable.com/docs/6.2.2/Options.html
        contextMenu: if value from table_options is True, still use default
        language: if value is not in table_options, attempt to get from environment
        """

        collected_table_options = DEFAULT_TABLE_OPTIONS.copy()

        if table_options is not None:
            if table_options.get("contextMenu", None) is True:
                # explicitly check for True, as value could also be array
                # delete to ensure the above default is kept for contextMenu
                del table_options["contextMenu"]
            collected_table_options.update(table_options)

        if "language" not in collected_table_options:
            # attempt to gather the current set language of not provided
            language = translation.get_language()
            collected_table_options["language"] = language

        return collected_table_options

    class Meta:
        default = None
        template = "table_block/blocks/table.html"
        icon = "table"
