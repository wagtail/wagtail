import uuid
from collections import OrderedDict, defaultdict
from collections.abc import Sequence

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms.utils import ErrorList
from django.utils.functional import cached_property
from django.utils.html import format_html_join
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.blocks.utils import BlockData
from .base import Block, BoundBlock, DeclarativeSubBlocksMetaclass

__all__ = ['BaseStreamBlock', 'StreamBlock', 'StreamValue', 'StreamBlockValidationError']


class StreamBlockValidationError(ValidationError):
    def __init__(self, block_errors=None, non_block_errors=None):
        params = {}
        if block_errors:
            params.update(block_errors)
        if non_block_errors:
            params[NON_FIELD_ERRORS] = non_block_errors
        super().__init__(
            'Validation error in StreamBlock', params=params)


class BaseStreamBlock(Block):

    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super().__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self.child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

        self.dependencies = self.child_blocks.values()

    def get_default(self):
        """
        Default values set on a StreamBlock should be a list of (type_name, value) tuples -
        we can't use StreamValue directly, because that would require a reference back to
        the StreamBlock that hasn't been built yet.

        For consistency, then, we need to convert it to a StreamValue here for StreamBlock
        to work with.
        """
        return StreamValue(self, self.meta.default)

    def value_from_datadict(self, data, files, prefix):
        return StreamValue(self, [(
            child_block_data['type'],
            self.child_blocks[child_block_data['type']]
            .value_from_datadict(child_block_data, files, prefix,),
            child_block_data.get('id', str(uuid.uuid4()))
        ) for child_block_data in data['value']
            if child_block_data['type'] in self.child_blocks
        ])

    @property
    def required(self):
        return self.meta.required

    def prepare_value(self, value, errors=None):
        if value is None:
            return []
        children_errors = ({} if errors is None
                           else errors.as_data()[0].params)
        prepared_value = []
        for i, stream_child in enumerate(value):
            child_errors = children_errors.get(i)
            child_block = stream_child.block
            child_value = stream_child.value
            html = child_block.get_instance_html(child_value,
                                                 errors=child_errors)
            child_value = BlockData({
                'id': stream_child.id or str(uuid.uuid4()),
                'type': child_block.name,
                'hasError': bool(child_errors),
                'value': child_block.prepare_value(child_value,
                                                   errors=child_errors),
            })
            if html is not None:
                child_value['html'] = html
            prepared_value.append(child_value)
        return prepared_value

    @cached_property
    def definition(self):
        definition = super(BaseStreamBlock, self).definition
        definition.update(
            children=[
                child_block.definition
                for child_block in self.child_blocks.values()
            ],
            minNum=self.meta.min_num,
            maxNum=self.meta.max_num,
        )
        html = self.get_instance_html([])
        if html is not None:
            definition['html'] = html
        return definition

    def clean(self, value):
        cleaned_data = []
        errors = {}
        non_block_errors = ErrorList()
        for i, child in enumerate(value):  # child is a StreamChild instance
            try:
                cleaned_data.append(
                    (child.block.name, child.block.clean(child.value), child.id)
                )
            except ValidationError as e:
                errors[i] = ErrorList([e])

        if self.meta.min_num is not None and self.meta.min_num > len(value):
            non_block_errors.append(ValidationError(
                _('The minimum number of items is %d') % self.meta.min_num
            ))
        elif self.required and len(value) == 0:
            non_block_errors.append(ValidationError(_('This field is required.')))

        if self.meta.max_num is not None and self.meta.max_num < len(value):
            non_block_errors.append(ValidationError(
                _('The maximum number of items is %d') % self.meta.max_num
            ))

        if self.meta.block_counts:
            block_counts = defaultdict(int)
            for item in value:
                block_counts[item.block_type] += 1

            for block_name, min_max in self.meta.block_counts.items():
                block = self.child_blocks[block_name]
                max_num = min_max.get('max_num', None)
                min_num = min_max.get('min_num', None)
                block_count = block_counts[block_name]
                if min_num is not None and min_num > block_count:
                    non_block_errors.append(ValidationError(
                        '{}: {}'.format(block.label, _('The minimum number of items is %d') % min_num)
                    ))
                if max_num is not None and max_num < block_count:
                    non_block_errors.append(ValidationError(
                        '{}: {}'.format(block.label, _('The maximum number of items is %d') % max_num)
                    ))

        if errors or non_block_errors:
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' list
            raise StreamBlockValidationError(block_errors=errors, non_block_errors=non_block_errors)

        return StreamValue(self, cleaned_data)

    def to_python(self, value):
        # the incoming JSONish representation is a list of dicts, each with a 'type' and 'value' field
        # (and possibly an 'id' too).
        # This is passed to StreamValue to be expanded lazily - but first we reject any unrecognised
        # block types from the list
        return StreamValue(self, [
            child_data for child_data in value
            if child_data['type'] in self.child_blocks
        ], is_lazy=True)

    def get_prep_value(self, value):
        if not value:
            # Falsy values (including None, empty string, empty list, and
            # empty StreamValue) become an empty stream
            return []
        else:
            # value is a StreamValue - delegate to its get_prep_value() method
            # (which has special-case handling for lazy StreamValues to avoid useless
            # round-trips to the full data representation and back)
            return value.get_prep_value()

    def get_api_representation(self, value, context=None):
        if value is None:
            # treat None as identical to an empty stream
            return []

        return [
            {
                'type': child.block.name,
                'value': child.block.get_api_representation(child.value, context=context),
                'id': child.id
            }
            for child in value  # child is a StreamChild instance
        ]

    def render_basic(self, value, context=None):
        return format_html_join(
            '\n', '<div class="block-{1}">{0}</div>',
            [
                (child.render(context=context), child.block_type)
                for child in value
            ]
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
        path = 'wagtail.core.blocks.StreamBlock'
        args = [list(self.child_blocks.items())]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"
        default = []
        required = True
        min_num = None
        max_num = None
        block_counts = {}


class StreamBlock(BaseStreamBlock, metaclass=DeclarativeSubBlocksMetaclass):
    pass


class StreamValue(Sequence):
    """
    Custom type used to represent the value of a StreamBlock; behaves as a sequence of BoundBlocks
    (which keep track of block types in a way that the values alone wouldn't).
    """

    class StreamChild(BoundBlock):
        """
        Extends BoundBlock with methods that make logical sense in the context of
        children of StreamField, but not necessarily elsewhere that BoundBlock is used
        """

        def __init__(self, *args, **kwargs):
            self.id = kwargs.pop('id')
            super(StreamValue.StreamChild, self).__init__(*args, **kwargs)

        @property
        def block_type(self):
            """
            Syntactic sugar so that we can say child.block_type instead of child.block.name.
            (This doesn't belong on BoundBlock itself because the idea of block.name denoting
            the child's "type" ('heading', 'paragraph' etc) is unique to StreamBlock, and in the
            wider context people are liable to confuse it with the block class (CharBlock etc).
            """
            return self.block.name

    def __init__(self, stream_block, stream_data, is_lazy=False, raw_text=None):
        """
        Construct a StreamValue linked to the given StreamBlock,
        with child values given in stream_data.

        Passing is_lazy=True means that stream_data is raw JSONish data as stored
        in the database, and needs to be converted to native values
        (using block.to_python()) when accessed. In this mode, stream_data is a
        list of dicts, each containing 'type' and 'value' keys.

        Passing is_lazy=False means that stream_data consists of immediately usable
        native values. In this mode, stream_data is a list of (type_name, value)
        or (type_name, value, id) tuples.

        raw_text exists solely as a way of representing StreamField content that is
        not valid JSON; this may legitimately occur if an existing text field is
        migrated to a StreamField. In this situation we return a blank StreamValue
        with the raw text accessible under the `raw_text` attribute, so that migration
        code can be rewritten to convert it as desired.
        """
        self.is_lazy = is_lazy
        self.stream_block = stream_block  # the StreamBlock object that handles this value
        self.stream_data = stream_data  # a list of (type_name, value) tuples
        self._bound_blocks = {}  # populated lazily from stream_data as we access items through __getitem__
        self.raw_text = raw_text

    def __getitem__(self, i):
        if i not in self._bound_blocks:
            if self.is_lazy:
                raw_value = self.stream_data[i]
                type_name = raw_value['type']
                child_block = self.stream_block.child_blocks[type_name]
                if hasattr(child_block, 'bulk_to_python'):
                    self._prefetch_blocks(type_name, child_block)
                    return self._bound_blocks[i]
                else:
                    value = child_block.to_python(raw_value['value'])
                    block_id = raw_value.get('id')
            else:
                try:
                    type_name, value, block_id = self.stream_data[i]
                except ValueError:
                    type_name, value = self.stream_data[i]
                    block_id = None

                child_block = self.stream_block.child_blocks[type_name]

            self._bound_blocks[i] = StreamValue.StreamChild(child_block, value, id=block_id)

        return self._bound_blocks[i]

    def _prefetch_blocks(self, type_name, child_block):
        """Prefetch all child blocks for the given `type_name` using the
        given `child_blocks`.

        This prevents n queries for n blocks of a specific type.
        """
        # create a mapping of all the child blocks matching the given block type,
        # mapping (index within the stream) => (raw block value)
        raw_values = OrderedDict(
            (i, item['value']) for i, item in enumerate(self.stream_data)
            if item['type'] == type_name
        )
        # pass the raw block values to bulk_to_python as a list
        converted_values = child_block.bulk_to_python(raw_values.values())

        # reunite the converted values with their stream indexes
        for i, value in zip(raw_values.keys(), converted_values):
            # also pass the block ID to StreamChild, if one exists for this stream index
            block_id = self.stream_data[i].get('id')
            self._bound_blocks[i] = StreamValue.StreamChild(child_block, value, id=block_id)

    def get_prep_value(self):
        prep_value = []

        for i, stream_data_item in enumerate(self.stream_data):
            if self.is_lazy and i not in self._bound_blocks:
                # This child has not been accessed as a bound block, so its raw JSONish
                # value (stream_data_item here) is still valid
                prep_value_item = stream_data_item

                # As this method is preparing this value to be saved to the database,
                # this is an appropriate place to ensure that each block has a unique id.
                prep_value_item['id'] = prep_value_item.get('id', str(uuid.uuid4()))

            else:
                # convert the bound block back into JSONish data
                child = self[i]
                # As this method is preparing this value to be saved to the database,
                # this is an appropriate place to ensure that each block has a unique id.
                child.id = child.id or str(uuid.uuid4())
                prep_value_item = {
                    'type': child.block.name,
                    'value': child.block.get_prep_value(child.value),
                    'id': child.id,
                }

            prep_value.append(prep_value_item)

        return prep_value

    def __eq__(self, other):
        if not isinstance(other, StreamValue):
            return False

        return self.stream_data == other.stream_data

    def __len__(self):
        return len(self.stream_data)

    def __repr__(self):
        return repr(list(self))

    def render_as_block(self, context=None):
        return self.stream_block.render(self, context=context)

    def __html__(self):
        return self.stream_block.render(self)

    def __str__(self):
        return self.__html__()
