"""
The ``assertCanCreate`` method requires page data to be passed in
the same format that the page edit form would submit. For complex
page types, it can be difficult to construct this data structure by hand;
the ``wagtail.test.utils.form_data`` module provides a set of helper
functions to assist with this.
"""

import json

import bs4
from django.http import QueryDict

from wagtail.admin.rich_text import get_rich_text_editor_widget

from .wagtail_tests import WagtailTestUtils


def _nested_form_data(data):
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = enumerate(data)

    for key, value in items:
        key = str(key)
        if isinstance(value, (dict, list)):
            for child_keys, child_value in _nested_form_data(value):
                yield [key] + child_keys, child_value
        else:
            yield [key], value


def nested_form_data(data):
    """
    Translates a nested dict structure into a flat form data dict
    with hyphen-separated keys.

    .. code-block:: python

        nested_form_data({
            'foo': 'bar',
            'parent': {
                'child': 'field',
            },
        })
        # Returns: {'foo': 'bar', 'parent-child': 'field'}
    """
    return {"-".join(key): value for key, value in _nested_form_data(data)}


def streamfield(items):
    """
    Takes a list of (block_type, value) tuples and turns it in to
    StreamField form data. Use this within a :func:`nested_form_data`
    call, with the field name as the key.

    .. code-block:: python

        nested_form_data({'content': streamfield([
            ('text', 'Hello, world'),
        ])})
        # Returns:
        # {
        #     'content-count': '1',
        #     'content-0-type': 'text',
        #     'content-0-value': 'Hello, world',
        #     'content-0-order': '0',
        #     'content-0-deleted': '',
        # }
    """

    def to_block(index, item):
        block, value = item
        return {"type": block, "value": value, "deleted": "", "order": str(index)}

    data_dict = {str(index): to_block(index, item) for index, item in enumerate(items)}
    data_dict["count"] = str(len(data_dict))
    return data_dict


def inline_formset(items, initial=0, min=0, max=1000):
    """
    Takes a list of form data for an InlineFormset and translates
    it in to valid POST data. Use this within a :func:`nested_form_data`
    call, with the formset relation name as the key.

    .. code-block:: python

        nested_form_data({'lines': inline_formset([
            {'text': 'Hello'},
            {'text': 'World'},
        ])})
        # Returns:
        # {
        #     'lines-TOTAL_FORMS': '2',
        #     'lines-INITIAL_FORMS': '0',
        #     'lines-MIN_NUM_FORMS': '0',
        #     'lines-MAX_NUM_FORMS': '1000',
        #     'lines-0-text': 'Hello',
        #     'lines-0-ORDER': '0',
        #     'lines-0-DELETE': '',
        #     'lines-1-text': 'World',
        #     'lines-1-ORDER': '1',
        #     'lines-1-DELETE': '',
        # }
    """

    def to_form(index, item):
        defaults = {
            "ORDER": str(index),
            "DELETE": "",
        }
        defaults.update(item)
        return defaults

    data_dict = {str(index): to_form(index, item) for index, item in enumerate(items)}

    data_dict.update(
        {
            "TOTAL_FORMS": str(len(data_dict)),
            "INITIAL_FORMS": str(initial),
            "MIN_NUM_FORMS": str(min),
            "MAX_NUM_FORMS": str(max),
        }
    )
    return data_dict


def rich_text(value, editor="default", features=None):
    """
    Converts an HTML-like rich text string to the data format required by
    the currently active rich text editor.

    :param editor: An alternative editor name as defined in ``WAGTAILADMIN_RICH_TEXT_EDITORS``
    :param features: A list of features allowed in the rich text content (see :ref:`rich_text_features`)

    .. code-block:: python

        self.assertCanCreate(root_page, ContentPage, nested_form_data({
            'title': 'About us',
            'body': rich_text('<p>Lorem ipsum dolor sit amet</p>'),
        }))
    """
    widget = get_rich_text_editor_widget(editor, features)
    return widget.format_value(value)


def _block_state_to_form_data(val, prefix, data):
    if isinstance(val, list):
        data[f"{prefix}-count"] = str(len(val))
        for i, item in enumerate(val):
            data[f"{prefix}-{i}-deleted"] = ""
            data[f"{prefix}-{i}-order"] = str(i)
            if isinstance(item, dict):
                if item.get("id") is not None:
                    data[f"{prefix}-{i}-id"] = str(item["id"])
                if "type" in item:
                    data[f"{prefix}-{i}-type"] = str(item["type"])
                    if "value" in item:
                        _block_state_to_form_data(
                            item["value"], f"{prefix}-{i}-value", data
                        )
                elif "value" in item:
                    _block_state_to_form_data(
                        item["value"], f"{prefix}-{i}-value", data
                    )
                else:
                    _block_state_to_form_data(item, f"{prefix}-{i}-value", data)
            else:
                _block_state_to_form_data(item, f"{prefix}-{i}-value", data)
    elif isinstance(val, dict):
        if ("edit_url" in val or "editUrl" in val) and "id" in val:
            data[prefix] = str(val["id"]) if val["id"] is not None else ""
        elif "columns" in val and "rows" in val:
            data[f"{prefix}-caption"] = str(val.get("caption") or "")
            columns = val.get("columns", [])
            data[f"{prefix}-column-count"] = str(len(columns))
            for i, col in enumerate(columns):
                data[f"{prefix}-column-{i}-deleted"] = ""
                data[f"{prefix}-column-{i}-order"] = str(i)
                data[f"{prefix}-column-{i}-type"] = str(col.get("type", ""))
                data[f"{prefix}-column-{i}-heading"] = str(col.get("heading", ""))
            rows = val.get("rows", [])
            data[f"{prefix}-row-count"] = str(len(rows))
            for r, row in enumerate(rows):
                data[f"{prefix}-row-{r}-deleted"] = ""
                data[f"{prefix}-row-{r}-order"] = str(r)
                for c, cell_val in enumerate(row.get("values", [])):
                    _block_state_to_form_data(cell_val, f"{prefix}-cell-{r}-{c}", data)
        else:
            for k, v in val.items():
                _block_state_to_form_data(v, f"{prefix}-{k}", data)
    elif isinstance(val, bool):
        if val:
            data[prefix] = "true"
    elif val is None:
        data[prefix] = ""
    else:
        data[prefix] = str(val)


def _querydict_from_form(form: bs4.Tag, exclude_csrf: bool = True) -> QueryDict:
    data = QueryDict(mutable=True)
    for input in form.find_all("input"):
        name = input.attrs.get("name")
        if (
            name
            and input.attrs.get("type", "") not in ("checkbox", "radio")
            and (not exclude_csrf or name != "csrfmiddlewaretoken")
        ):
            data[name] = input.attrs.get("value", "")

    for input in form.find_all("input", type="radio", checked=True):
        name = input.attrs.get("name")
        if name:
            data[name] = input.attrs.get("value")

    for input in form.find_all("input", type="checkbox", checked=True):
        name = input.attrs.get("name")
        if name:
            data.appendlist(name, input.attrs.get("value", ""))

    for textarea in form.find_all("textarea"):
        name = textarea.attrs.get("name")
        if name:
            data[name] = textarea.get_text()

    for select in form.find_all("select"):
        name = select.attrs.get("name")
        if name:
            selected_value = False
            for option in select.find_all("option", selected=True):
                selected_value = True
                data.appendlist(name, option.attrs.get("value", option.get_text()))
            if not selected_value:
                first_option = select.find("option")
                if first_option:
                    data[name] = first_option.attrs.get(
                        "value", first_option.get_text()
                    )

    for block in form.find_all(attrs={"data-block": True}):
        name = block.attrs.get("name") or block.attrs.get("id")
        args_attr = block.attrs.get("data-w-block-arguments-value")
        if name and args_attr:
            try:
                args = json.loads(args_attr)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            if isinstance(args, (list, tuple)) and len(args) > 0:
                _block_state_to_form_data(args[0], name, data)

    return data


def querydict_from_html(
    html: str, form_id: str = None, form_index: int = 0, exclude_csrf: bool = True
) -> QueryDict:
    soup = WagtailTestUtils.get_soup(html)
    if form_id is not None:
        form = soup.find("form", attrs={"id": form_id})
        if form is None:
            raise ValueError(f'No form was found with id "{form_id}".')
        return _querydict_from_form(form, exclude_csrf)
    else:
        index = int(form_index)
        for i, form in enumerate(soup.find_all("form", limit=index + 1)):
            if i == index:
                return _querydict_from_form(form, exclude_csrf)
    raise ValueError(f"No form was found with index: {form_index}.")
