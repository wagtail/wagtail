import collections

from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join

from .base import Block, DeclarativeSubBlocksMetaclass
from .utils import js_dict

__all__ = ['BaseStructBlock', 'StructBlock', 'StructValue']


class StructValue(collections.OrderedDict):
    """ A class that generates a StructBlock value from provded sub-blocks """
    def __init__(self, block, *args):
        super().__init__(*args)
        self.block = block

    def __html__(self):
        return self.block.render(self)

    def render_as_block(self, context=None):
        return self.block.render(self, context=context)

    @cached_property
    def bound_blocks(self):
        return collections.OrderedDict([
            (name, block.bind(self.get(name)))
            for name, block in self.block.child_blocks.items()
        ])


class BaseStructBlock(Block):

    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super().__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self.child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

        self.child_js_initializers = {}
        for name, block in self.child_blocks.items():
            js_initializer = block.js_initializer()
            if js_initializer is not None:
                self.child_js_initializers[name] = js_initializer

        self.dependencies = self.child_blocks.values()

    def get_default(self):
        """
        Any default value passed in the constructor or self.meta is going to be a dict
        rather than a StructValue; for consistency, we need to convert it to a StructValue
        for StructBlock to work with
        """
        return self._to_struct_value(self.meta.default.items())

    def js_initializer(self):
        # skip JS setup entirely if no children have js_initializers
        if not self.child_js_initializers:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_initializers)

    @property
    def media(self):
        return forms.Media(js=[static('wagtailadmin/js/blocks/struct.js')])

    def get_form_context(self, value, prefix='', errors=None):
        if errors:
            if len(errors) > 1:
                # We rely on StructBlock.clean throwing a single ValidationError with a specially crafted
                # 'params' attribute that we can pull apart and distribute to the child blocks
                raise TypeError('StructBlock.render_form unexpectedly received multiple errors')
            error_dict = errors.as_data()[0].params
        else:
            error_dict = {}

        bound_child_blocks = collections.OrderedDict([
            (
                name,
                block.bind(value.get(name, block.get_default()),
                           prefix="%s-%s" % (prefix, name), errors=error_dict.get(name))
            )
            for name, block in self.child_blocks.items()
        ])

        return {
            'children': bound_child_blocks,
            'help_text': getattr(self.meta, 'help_text', None),
            'classname': self.meta.form_classname,
            'block_definition': self,
            'prefix': prefix,
        }

    def render_form(self, value, prefix='', errors=None):
        context = self.get_form_context(value, prefix=prefix, errors=errors)

        return render_to_string(self.meta.form_template, context)

    def value_from_datadict(self, data, files, prefix):
        return self._to_struct_value([
            (name, block.value_from_datadict(data, files, '%s-%s' % (prefix, name)))
            for name, block in self.child_blocks.items()
        ])

    def value_omitted_from_data(self, data, files, prefix):
        return all(
            block.value_omitted_from_data(data, files, '%s-%s' % (prefix, name))
            for name, block in self.child_blocks.items()
        )

    def clean(self, value):
        result = []  # build up a list of (name, value) tuples to be passed to the StructValue constructor
        errors = {}
        for name, val in value.items():
            try:
                result.append((name, self.child_blocks[name].clean(val)))
            except ValidationError as e:
                errors[name] = ErrorList([e])

        if errors:
            # The message here is arbitrary - StructBlock.render_form will suppress it
            # and delegate the errors contained in the 'params' dict to the child blocks instead
            raise ValidationError('Validation error in StructBlock', params=errors)

        return self._to_struct_value(result)

    def to_python(self, value):
        """ Recursively call to_python on children and return as a StructValue """
        return self._to_struct_value([
            (
                name,
                (child_block.to_python(value[name]) if name in value else child_block.get_default())
                # NB the result of get_default is NOT passed through to_python, as it's expected
                # to be in the block's native type already
            )
            for name, child_block in self.child_blocks.items()
        ])

    def _to_struct_value(self, block_items):
        """ Return a Structvalue representation of the sub-blocks in this block """
        return self.meta.value_class(self, block_items)

    def get_prep_value(self, value):
        """ Recursively call get_prep_value on children and return as a plain dict """
        return dict([
            (name, self.child_blocks[name].get_prep_value(val))
            for name, val in value.items()
        ])

    def get_api_representation(self, value, context=None):
        """ Recursively call get_api_representation on children and return as a plain dict """
        return dict([
            (name, self.child_blocks[name].get_api_representation(val, context=context))
            for name, val in value.items()
        ])

    def get_searchable_content(self, value):
        content = []

        for name, block in self.child_blocks.items():
            content.extend(block.get_searchable_content(value.get(name, block.get_default())))

        return content

    def deconstruct(self):
        """
        Always deconstruct StructBlock instances as if they were plain StructBlocks with all of the
        field definitions passed to the constructor - even if in reality this is a subclass of StructBlock
        with the fields defined declaratively, or some combination of the two.

        This ensures that the field definitions get frozen into migrations, rather than leaving a reference
        to a custom subclass in the user's models.py that may or may not stick around.
        """
        path = 'wagtail.core.blocks.StructBlock'
        args = [list(self.child_blocks.items())]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    def render_basic(self, value, context=None):
        return format_html('<dl>\n{}\n</dl>', format_html_join(
            '\n', '    <dt>{}</dt>\n    <dd>{}</dd>', value.items()))

    class Meta:
        default = {}
        form_classname = 'struct-block'
        form_template = 'wagtailadmin/block_forms/struct.html'
        value_class = StructValue
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"


class StructBlock(BaseStructBlock, metaclass=DeclarativeSubBlocksMetaclass):
    pass
