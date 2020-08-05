from uuid import uuid4

from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.core.blocks.utils import BlockData
from .base import Block

__all__ = ['ListBlock']


class ListBlock(Block):

    def __init__(self, child_block, **kwargs):
        super().__init__(**kwargs)
        # child_block may be passed as a class, so we may have to instantiate
        self.child_block = (child_block() if isinstance(child_block, type)
                            else child_block)

        if not hasattr(self.meta, 'default'):
            # Default to a list consisting
            # of one empty (i.e. default-valued) child item
            self.meta.default = [self.child_block.get_default()]

        self.dependencies = [self.child_block]

    def value_from_datadict(self, data, files, prefix):
        return [self.child_block.value_from_datadict(child_block_data, files,
                                                     prefix)
                for child_block_data in data['value']]

    def prepare_value(self, value, errors=None):
        children_errors = (None if errors is None
                           else errors.as_data()[0].params)
        if children_errors is None:
            children_errors = [None] * len(value)
        prepared_value = []
        for child_value, child_errors in zip(value, children_errors):
            html = self.child_block.get_instance_html(child_value,
                                                      errors=child_errors)
            child_value = BlockData({
                'id': str(uuid4()),
                'type': self.child_block.name,
                'hasError': bool(child_errors),
                'value': self.child_block.prepare_value(child_value,
                                                        errors=errors),
            })
            if html is not None:
                child_value['html'] = html
            prepared_value.append(child_value)
        return prepared_value

    @cached_property
    def definition(self):
        definition = super(ListBlock, self).definition
        definition.update(
            children=[self.child_block.definition],
            minNum=self.meta.min_num,
            maxNum=self.meta.max_num,
        )
        html = self.get_instance_html([])
        if html is not None:
            definition['html'] = html
        return definition

    def clean(self, value):
        result = []
        errors = []
        for child_val in value:
            try:
                result.append(self.child_block.clean(child_val))
            except ValidationError as e:
                errors.append(ErrorList([e]))
            else:
                errors.append(None)

        if any(errors):
            raise ValidationError('Validation error in ListBlock',
                                  params=errors)

        if self.meta.min_num is not None and self.meta.min_num > len(value):
            raise ValidationError(
                _('The minimum number of items is %d') % self.meta.min_num
            )
        elif self.required and len(value) == 0:
            raise ValidationError(_('This field is required.'))

        if self.meta.max_num is not None and self.meta.max_num < len(value):
            raise ValidationError(
                _('The maximum number of items is %d') % self.meta.max_num
            )

        return result

    def to_python(self, value):
        # If child block supports bulk retrieval, use it.
        if hasattr(self.child_block, 'bulk_to_python'):
            return self.child_block.bulk_to_python(value)

        # Otherwise recursively call to_python on each child and return as a list.
        return [
            self.child_block.to_python(item)
            for item in value
        ]

    def get_prep_value(self, value):
        # recursively call get_prep_value on children and return as a list
        return [
            self.child_block.get_prep_value(item)
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
        min_num = None
        max_num = None


DECONSTRUCT_ALIASES = {
    ListBlock: 'wagtail.core.blocks.ListBlock',
}
