from __future__ import absolute_import, unicode_literals

import collections

from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
# Must be imported from Django so we get the new implementation of with_metaclass
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

from .base import Block, DeclarativeSubBlocksMetaclass
from .utils import js_dict

__all__ = ['BaseStructBlock', 'StructBlock', 'StructValue']


class BaseStructBlock(Block):

    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super(BaseStructBlock, self).__init__(**kwargs)

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
        return StructValue(self, self.meta.default.items())

    def js_initializer(self):
        # skip JS setup entirely if no children have js_initializers
        if not self.child_js_initializers:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_initializers)

    @property
    def media(self):
        return forms.Media(js=[static('wagtailadmin/js/blocks/struct.js')])

    def render_form(self, value, prefix='', errors=None):
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

        return render_to_string(self.meta.form_template, {
            'children': bound_child_blocks,
            'help_text': getattr(self.meta, 'help_text', None),
            'classname': self.meta.form_classname,
        })

    def value_from_datadict(self, data, files, prefix):
        return StructValue(self, [
            (name, block.value_from_datadict(data, files, '%s-%s' % (prefix, name)))
            for name, block in self.child_blocks.items()
        ])

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

        return StructValue(self, result)

    def to_python(self, value):
        # recursively call to_python on children and return as a StructValue
        return StructValue(self, [
            (
                name,
                (child_block.to_python(value[name]) if name in value else child_block.get_default())
                # NB the result of get_default is NOT passed through to_python, as it's expected
                # to be in the block's native type already
            )
            for name, child_block in self.child_blocks.items()
        ])

    def get_prep_value(self, value):
        # recursively call get_prep_value on children and return as a plain dict
        return dict([
            (name, self.child_blocks[name].get_prep_value(val))
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
        path = 'wagtail.wagtailcore.blocks.StructBlock'
        args = [self.child_blocks.items()]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super(BaseStructBlock, self).check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    class Meta:
        default = {}
        template = "wagtailadmin/blocks/struct.html"
        form_classname = 'struct-block'
        form_template = 'wagtailadmin/block_forms/struct.html'
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"


class StructBlock(six.with_metaclass(DeclarativeSubBlocksMetaclass, BaseStructBlock)):
    pass


@python_2_unicode_compatible  # provide equivalent __unicode__ and __str__ methods on Py2
class StructValue(collections.OrderedDict):
    def __init__(self, block, *args):
        super(StructValue, self).__init__(*args)
        self.block = block

    def __str__(self):
        return self.block.render(self)

    @cached_property
    def bound_blocks(self):
        return collections.OrderedDict([
            (name, block.bind(self.get(name)))
            for name, block in self.block.child_blocks.items()
        ])
