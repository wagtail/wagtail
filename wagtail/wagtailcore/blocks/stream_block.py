from __future__ import absolute_import, unicode_literals

import collections

from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

import six

from wagtail.wagtailcore.utils import escape_script

from .base import Block, DeclarativeSubBlocksMetaclass, BoundBlock
from .utils import indent, js_dict


__all__ = ['BaseStreamBlock', 'StreamBlock', 'StreamValue']


class BaseStreamBlock(Block):
    # TODO: decide what it means to pass a 'default' arg to StreamBlock's constructor. Logically we want it to be
    # of type StreamValue, but we can't construct one of those because it needs a reference back to the StreamBlock
    # that we haven't constructed yet...
    class Meta:
        @property
        def default(self):
            return StreamValue(self, [])

    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super(BaseStreamBlock, self).__init__(**kwargs)

        self.child_blocks = self.base_blocks.copy()  # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

        self.dependencies = self.child_blocks.values()

    def render_list_member(self, block_type_name, value, prefix, index, errors=None):
        """
        Render the HTML for a single list item. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state/type, delete/reorder buttons, and the child block's own HTML.
        """
        child_block = self.child_blocks[block_type_name]
        child = child_block.bind(value, prefix="%s-value" % prefix, errors=errors)
        return render_to_string('wagtailadmin/block_forms/stream_member.html', {
            'child_blocks': self.child_blocks.values(),
            'block_type_name': block_type_name,
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        return format_html_join(
            '\n', '<script type="text/template" id="{0}-newmember-{1}">{2}</script>',
            [
                (
                    self.definition_prefix,
                    name,
                    mark_safe(escape_script(self.render_list_member(name, child_block.meta.default, '__PREFIX__', '')))
                )
                for name, child_block in self.child_blocks.items()
            ]
        )

    @property
    def media(self):
        return forms.Media(js=['wagtailadmin/js/blocks/sequence.js', 'wagtailadmin/js/blocks/stream.js'])

    def js_initializer(self):
        # compile a list of info dictionaries, one for each available block type
        child_blocks = []
        for name, child_block in self.child_blocks.items():
            # each info dictionary specifies at least a block name
            child_block_info = {'name': "'%s'" % name}

            # if the child defines a JS initializer function, include that in the info dict
            # along with the param that needs to be passed to it for initializing an empty/default block
            # of that type
            child_js_initializer = child_block.js_initializer()
            if child_js_initializer:
                child_block_info['initializer'] = child_js_initializer

            child_blocks.append(indent(js_dict(child_block_info)))

        opts = {
            'definitionPrefix': "'%s'" % self.definition_prefix,
            'childBlocks': '[\n%s\n]' % ',\n'.join(child_blocks),
        }

        return "StreamBlock(%s)" % js_dict(opts)

    def render_form(self, value, prefix='', errors=None):
        if errors:
            if len(errors) > 1:
                # We rely on ListBlock.clean throwing a single ValidationError with a specially crafted
                # 'params' attribute that we can pull apart and distribute to the child blocks
                raise TypeError('ListBlock.render_form unexpectedly received multiple errors')
            error_list = errors.as_data()[0].params
        else:
            error_list = None

        # drop any child values that are an unrecognised block type
        valid_children = [child for child in value if child.block_type in self.child_blocks]

        list_members_html = [
            self.render_list_member(child.block_type, child.value, "%s-%d" % (prefix, i), i,
                errors=error_list[i] if error_list else None)
            for (i, child) in enumerate(valid_children)
        ]

        return render_to_string('wagtailadmin/block_forms/stream.html', {
            'label': self.label,
            'prefix': prefix,
            'list_members_html': list_members_html,
            'child_blocks': self.child_blocks.values(),
            'header_menu_prefix': '%s-before' % prefix,
        })

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                continue
            block_type_name = data['%s-%d-type' % (prefix, i)]
            try:
                child_block = self.child_blocks[block_type_name]
            except KeyError:
                continue

            values_with_indexes.append(
                (
                    int(data['%s-%d-order' % (prefix, i)]),
                    block_type_name,
                    child_block.value_from_datadict(data, files, '%s-%d-value' % (prefix, i)),
                )
            )

        values_with_indexes.sort()
        return StreamValue(self, [
            (child_block_type_name, value)
            for (index, child_block_type_name, value) in values_with_indexes
        ])

    def clean(self, value):
        cleaned_data = []
        errors = []
        for child in value:  # child is a BoundBlock instance
            try:
                cleaned_data.append(
                    (child.block.name, child.block.clean(child.value))
                )
            except ValidationError as e:
                errors.append(ErrorList([e]))
            else:
                errors.append(None)

        if any(errors):
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' list
            raise ValidationError('Validation error in StreamBlock', params=errors)

        return StreamValue(self, cleaned_data)

    def to_python(self, value):
        # the incoming JSONish representation is a list of dicts, each with a 'type' and 'value' field.
        # Convert this to a StreamValue backed by a list of (type, value) tuples
        return StreamValue(self, [
            (child_data['type'], self.child_blocks[child_data['type']].to_python(child_data['value']))
            for child_data in value
            if child_data['type'] in self.child_blocks
        ])

    def get_prep_value(self, value):
        if value is None:
            # treat None as identical to an empty stream
            return []

        return [
            {'type': child.block.name, 'value': child.block.get_prep_value(child.value)}
            for child in value  # child is a BoundBlock instance
        ]

    def render_basic(self, value):
        return format_html_join('\n', '<div class="block-{1}">{0}</div>',
            [(force_text(child), child.block_type) for child in value]
        )

    def get_searchable_content(self, value):
        content = []

        for child in value:
            content.extend(child.block.get_searchable_content(child.value))

        return content

    def deconstruct(self):
        """
        Always deconstruct StreamBlock instances as if they were plain StreamBlocks with all of the
        field definitions passed to the constructor - even if in reality this is a subclass of StreamBlock
        with the fields defined declaratively, or some combination of the two.

        This ensures that the field definitions get frozen into migrations, rather than leaving a reference
        to a custom subclass in the user's models.py that may or may not stick around.
        """
        path = 'wagtail.wagtailcore.blocks.StreamBlock'
        args = [self.child_blocks.items()]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)


class StreamBlock(six.with_metaclass(DeclarativeSubBlocksMetaclass, BaseStreamBlock)):
    pass


@python_2_unicode_compatible  # provide equivalent __unicode__ and __str__ methods on Py2
class StreamValue(collections.Sequence):
    """
    Custom type used to represent the value of a StreamBlock; behaves as a sequence of BoundBlocks
    (which keep track of block types in a way that the values alone wouldn't).
    """

    @python_2_unicode_compatible
    class StreamChild(BoundBlock):
        """Provides some extensions to BoundBlock to make it more natural to work with on front-end templates"""
        def __str__(self):
            """Render the value according to the block's native rendering"""
            return self.block.render(self.value)

        @property
        def block_type(self):
            """
            Syntactic sugar so that we can say child.block_type instead of child.block.name.
            (This doesn't belong on BoundBlock itself because the idea of block.name denoting
            the child's "type" ('heading', 'paragraph' etc) is unique to StreamBlock, and in the
            wider context people are liable to confuse it with the block class (CharBlock etc).
            """
            return self.block.name

    def __init__(self, stream_block, stream_data):
        self.stream_block = stream_block  # the StreamBlock object that handles this value
        self.stream_data = stream_data  # a list of (type_name, value) tuples
        self._bound_blocks = {}  # populated lazily from stream_data as we access items through __getitem__

    def __getitem__(self, i):
        if i not in self._bound_blocks:
            type_name, value = self.stream_data[i]
            child_block = self.stream_block.child_blocks[type_name]
            self._bound_blocks[i] = StreamValue.StreamChild(child_block, value)

        return self._bound_blocks[i]

    def __len__(self):
        return len(self.stream_data)

    def __repr__(self):
        return repr(list(self))

    def __str__(self):
        return self.stream_block.render(self)
