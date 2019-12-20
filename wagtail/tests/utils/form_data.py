"""
The ``assertCanCreate`` method requires page data to be passed in
the same format that the page edit form would submit. For complex
page types, it can be difficult to construct this data structure by hand;
the ``wagtail.tests.utils.form_data`` module provides a set of helper
functions to assist with this.
"""

from wagtail.admin.rich_text import get_rich_text_editor_widget


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
    return {'-'.join(key): value for key, value in _nested_form_data(data)}


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
        return {'type': block, 'value': value, 'deleted': '', 'order': str(index)}
    data_dict = {str(index): to_block(index, item)
                 for index, item in enumerate(items)}
    data_dict['count'] = str(len(data_dict))
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
            'ORDER': str(index),
            'DELETE': '',
        }
        defaults.update(item)
        return defaults

    data_dict = {str(index): to_form(index, item)
                 for index, item in enumerate(items)}

    data_dict.update({
        'TOTAL_FORMS': str(len(data_dict)),
        'INITIAL_FORMS': str(initial),
        'MIN_NUM_FORMS': str(min),
        'MAX_NUM_FORMS': str(max),
    })
    return data_dict


def rich_text(value, editor='default', features=None):
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
