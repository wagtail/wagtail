from typing import Any

from django.core.exceptions import ValidationError
from django.forms import BaseForm, Field
from django.utils.datastructures import MultiValueDict

from wagtail.blocks.base import BlockField
from wagtail.blocks.list_block import ListBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock


def flatten_block_value(block, value: Any, prefix: str, data: MultiValueDict) -> None:
    """Write ``value`` (in its StreamField API JSON shape) into ``data``.

    Mirrors each block type's own ``value_from_datadict`` key scheme in
    reverse, so ``block.value_from_datadict(data, {}, prefix)`` reconstructs
    ``value`` when the resulting form is bound. This lets a StreamField's
    real form field (and therefore any custom ``Block.clean()`` logic) run
    against JSON input, both at the top level and inside InlinePanel
    children.
    """
    if isinstance(block, BaseStreamBlock):
        items = value or []
        data[f"{prefix}-count"] = str(len(items))
        for i, item in enumerate(items):
            data[f"{prefix}-{i}-deleted"] = ""
            data[f"{prefix}-{i}-order"] = str(i)
            data[f"{prefix}-{i}-type"] = item["type"]
            if item.get("id") is not None:
                data[f"{prefix}-{i}-id"] = item["id"]
            try:
                child_block = block.child_blocks[item["type"]]
            except KeyError:
                raise ValidationError(
                    f"{prefix}: unrecognised block type {item['type']!r}"
                ) from None
            flatten_block_value(child_block, item["value"], f"{prefix}-{i}-value", data)
    elif isinstance(block, ListBlock):
        items = value or []
        data[f"{prefix}-count"] = str(len(items))
        for i, item in enumerate(items):
            data[f"{prefix}-{i}-deleted"] = ""
            data[f"{prefix}-{i}-order"] = str(i)
            flatten_block_value(block.child_block, item, f"{prefix}-{i}-value", data)
    elif isinstance(block, BaseStructBlock):
        value = value or {}
        for name, child_block in block.child_blocks.items():
            flatten_block_value(child_block, value.get(name), f"{prefix}-{name}", data)
    else:
        # A leaf field block (CharBlock, BooleanBlock, ChooserBlock, ...):
        # its own form field's widget reads a single key via plain `.get()`,
        # confirmed for every built-in Wagtail/Django block widget.
        data[prefix] = value


def _set_field_value(field: Field, name: str, value: Any, data: MultiValueDict) -> None:
    """Write ``value`` for a single (non-formset) form field into ``data``.

    Most widgets read a single key via plain ``.get()`` (confirmed for every
    built-in Wagtail/Django widget); the exceptions handled here are a
    ``BlockField`` (StreamField), whose widget needs its own flattened key
    scheme; a multi-valued field (e.g. ``ModelMultipleChoiceField`` for a
    ``ParentalManyToManyField``), whose widget calls ``getlist`` - so it's
    set via ``setlist`` rather than plain item assignment, which would wrap
    the whole list as a single value instead of storing it as the value list
    itself; and a rich text field's widget (e.g. Draftail), whose
    ``value_from_datadict`` always runs the raw value through
    ``self.converter.to_database_format()`` - assuming it's already in the
    editor's own submission format, not our plain database-format HTML
    string. ``format_value()`` is that converter's documented inverse
    (``from_database_format``), so round-tripping our HTML through it first,
    then letting ``value_from_datadict`` convert it back, works for whichever
    rich text editor a project has configured without needing to
    special-case Draftail specifically.
    """
    if isinstance(field, BlockField):
        flatten_block_value(field.block, value, name, data)
    elif getattr(field.widget, "allow_multiple_selected", False):
        data.setlist(name, list(value) if value else [])
    elif hasattr(field.widget, "converter"):
        # A rich text editor widget (Draftail's `to_database_format`/
        # `from_database_format` contract - core ships only Draftail, but
        # third-party editors may implement the same converter pattern).
        data[name] = field.widget.format_value(value)
    else:
        data[name] = value


def build_form_data(
    form: BaseForm,
    payload: dict[str, Any],
    formset_payloads: dict[str, list],
) -> MultiValueDict:
    """Build a ``MultiValueDict`` that binds ``form`` (and its child formsets,
    if it's a ``ClusterForm``) as if the equivalent HTML form had been
    submitted.

    ``payload`` supplies values for the top-level form's own fields, keyed by
    field name. ``formset_payloads`` supplies, for each InlinePanel-backed
    relation name declared on the form, a list of dicts (one per child, keyed
    by the child form's own field names) - both taken directly from the
    parsed JSON request body.

    Only fields the form actually declares are considered: a page model's
    ``api_fields`` may list more than a panel exposes, and an InlinePanel
    restricts its child form to its own panel fields, so surplus JSON keys
    are simply not looked up here (see ``InlinePanel.get_form_options``).
    """
    data = MultiValueDict()

    for name, field in form.fields.items():
        if name in payload:
            _set_field_value(field, name, payload[name], data)

    for rel_name, formset in getattr(form, "formsets", {}).items():
        items = formset_payloads.get(rel_name, [])
        prefix = formset.prefix
        data[f"{prefix}-TOTAL_FORMS"] = str(len(items))
        data[f"{prefix}-INITIAL_FORMS"] = "0"
        empty_form = formset.empty_form
        for i, item in enumerate(items):
            item_prefix = f"{prefix}-{i}"
            for field_name, field in empty_form.fields.items():
                if field_name in item:
                    _set_field_value(
                        field, f"{item_prefix}-{field_name}", item[field_name], data
                    )

    return data
