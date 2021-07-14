import itertools

from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.telepath import Adapter, register

from .base import Block, get_help_icon


__all__ = ['ListBlock', 'ListBlockValidationError']


class ListBlockValidationError(ValidationError):
    def __init__(self, block_errors=None, non_block_errors=None):
        self.non_block_errors = non_block_errors or ErrorList()
        self.block_errors = block_errors or []

        params = {}
        if block_errors:
            params['block_errors'] = block_errors
        if non_block_errors:
            params['non_block_errors'] = non_block_errors
        super().__init__('Validation error in ListBlock', params=params)


class ListBlockValidationErrorAdapter(Adapter):
    js_constructor = 'wagtail.blocks.ListBlockValidationError'

    def js_args(self, error):
        return [
            [elist.as_data() if elist is not None else elist for elist in error.block_errors],
            error.non_block_errors.as_data(),
        ]

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/telepath/blocks.js'),
        ])


register(ListBlockValidationErrorAdapter(), ListBlockValidationError)


class ListBlock(Block):

    def __init__(self, child_block, **kwargs):
        super().__init__(**kwargs)

        if isinstance(child_block, type):
            # child_block was passed as a class, so convert it to a block instance
            self.child_block = child_block()
        else:
            self.child_block = child_block

        if not hasattr(self.meta, 'default'):
            # Default to a list consisting of one empty (i.e. default-valued) child item
            self.meta.default = [self.child_block.get_default()]

    def get_default(self):
        # wrap with list() so that each invocation of get_default returns a distinct instance
        return list(self.meta.default)

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                continue
            values_with_indexes.append(
                (
                    int(data['%s-%d-order' % (prefix, i)]),
                    self.child_block.value_from_datadict(data, files, '%s-%d-value' % (prefix, i))
                )
            )

        values_with_indexes.sort()
        return [v for (i, v) in values_with_indexes]

    def value_omitted_from_data(self, data, files, prefix):
        return ('%s-count' % prefix) not in data

    def clean(self, value):
        result = []
        errors = []
        non_block_errors = ErrorList()
        for child_val in value:
            try:
                result.append(self.child_block.clean(child_val))
            except ValidationError as e:
                errors.append(ErrorList([e]))
            else:
                errors.append(None)

        if any(errors) or non_block_errors:
            raise ListBlockValidationError(block_errors=errors, non_block_errors=non_block_errors)

        return result

    def to_python(self, value):
        # 'value' is a list of child block values; use bulk_to_python to convert them all in one go
        return self.child_block.bulk_to_python(value)

    def bulk_to_python(self, values):
        # 'values' is a list of lists of child block values; concatenate them into one list so that
        # we can make a single call to child_block.bulk_to_python
        lengths = [len(val) for val in values]
        raw_values = list(itertools.chain.from_iterable(values))
        converted_values = self.child_block.bulk_to_python(raw_values)

        # split converted_values back into sub-lists of the original lengths
        result = []
        offset = 0
        for sublist_len in lengths:
            result.append(converted_values[offset:offset + sublist_len])
            offset += sublist_len

        return result

    def get_prep_value(self, value):
        # recursively call get_prep_value on children and return as a list
        return [
            self.child_block.get_prep_value(item)
            for item in value
        ]

    def get_form_state(self, value):
        return [
            self.child_block.get_form_state(item)
            for item in value
        ]

    def get_api_representation(self, value, context=None):
        # recursively call get_api_representation on children and return as a list
        return [
            self.child_block.get_api_representation(item, context=context)
            for item in value
        ]

    def render_basic(self, value, context=None):
        children = format_html_join(
            '\n', '<li>{0}</li>',
            [
                (self.child_block.render(child_value, context=context),)
                for child_value in value
            ]
        )
        return format_html("<ul>{0}</ul>", children)

    def get_searchable_content(self, value):
        content = []

        for child_value in value:
            content.extend(self.child_block.get_searchable_content(child_value))

        return content

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self.child_block.check(**kwargs))
        return errors

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"
        form_classname = None


class ListBlockAdapter(Adapter):
    js_constructor = 'wagtail.blocks.ListBlock'

    def js_args(self, block):
        meta = {
            'label': block.label, 'icon': block.meta.icon, 'classname': block.meta.form_classname,
            'strings': {
                'MOVE_UP': _("Move up"),
                'MOVE_DOWN': _("Move down"),
                'DUPLICATE': _("Duplicate"),
                'DELETE': _("Delete"),
                'ADD': _("Add"),
            },
        }
        help_text = getattr(block.meta, 'help_text', None)
        if help_text:
            meta['helpText'] = help_text
            meta['helpIcon'] = get_help_icon()

        return [
            block.name,
            block.child_block,
            block.child_block.get_form_state(block.child_block.get_default()),
            meta,
        ]

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/telepath/blocks.js'),
        ])


register(ListBlockAdapter(), ListBlock)


DECONSTRUCT_ALIASES = {
    ListBlock: 'wagtail.core.blocks.ListBlock',
}
