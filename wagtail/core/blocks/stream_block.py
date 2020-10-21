import uuid
import warnings

from collections import OrderedDict, defaultdict
from collections.abc import MutableSequence

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.utils import escape_script
from wagtail.utils.deprecation import RemovedInWagtail214Warning

from .base import Block, BoundBlock, DeclarativeSubBlocksMetaclass
from .utils import indent, js_dict


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

    def sorted_child_blocks(self):
        """Child blocks, sorted in to their groups."""
        return sorted(self.child_blocks.values(),
                      key=lambda child_block: child_block.meta.group)

    def render_list_member(self, block_type_name, value, prefix, index, errors=None, id=None):
        """
        Render the HTML for a single list item. This consists of a container, hidden fields
        to manage ID/deleted state/type, delete/reorder buttons, and the child block's own HTML.
        """
        child_block = self.child_blocks[block_type_name]
        child = child_block.bind(value, prefix="%s-value" % prefix, errors=errors)
        return render_to_string('wagtailadmin/block_forms/stream_member.html', {
            'child_blocks': self.sorted_child_blocks(),
            'block_type_name': block_type_name,
            'child_block': child_block,
            'prefix': prefix,
            'child': child,
            'index': index,
            'block_id': id,
        })

    def html_declarations(self):
        return format_html_join(
            '\n', '<script type="text/template" id="{0}-newmember-{1}">{2}</script>',
            [
                (
                    self.definition_prefix,
                    name,
                    mark_safe(escape_script(self.render_list_member(name, child_block.get_default(), '__PREFIX__', '')))
                )
                for name, child_block in self.child_blocks.items()
            ]
        )

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/blocks/sequence.js'),
            versioned_static('wagtailadmin/js/blocks/stream.js')
        ])

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
            'maxNumChildBlocks': 'Infinity' if self.meta.max_num is None else ('%s' % self.meta.max_num),
        }

        return "StreamBlock(%s)" % js_dict(opts)

    def render_form(self, value, prefix='', errors=None):
        error_dict = {}
        if errors:
            if len(errors) > 1:
                # We rely on StreamBlock.clean throwing a single
                # StreamBlockValidationError with a specially crafted 'params'
                # attribute that we can pull apart and distribute to the child
                # blocks
                raise TypeError('StreamBlock.render_form unexpectedly received multiple errors')
            error_dict = errors.as_data()[0].params

        # value can be None when the StreamField is in a formset
        if value is None:
            value = self.get_default()
        # drop any child values that are an unrecognised block type
        valid_children = [child for child in value if child.block_type in self.child_blocks]

        list_members_html = [
            self.render_list_member(child.block_type, child.value, "%s-%d" % (prefix, i), i,
                                    errors=error_dict.get(i), id=child.id)
            for (i, child) in enumerate(valid_children)
        ]

        return render_to_string('wagtailadmin/block_forms/stream.html', {
            'prefix': prefix,
            'help_text': getattr(self.meta, 'help_text', None),
            'list_members_html': list_members_html,
            'child_blocks': self.sorted_child_blocks(),
            'header_menu_prefix': '%s-before' % prefix,
            'block_errors': error_dict.get(NON_FIELD_ERRORS),
            'classname': getattr(self.meta, 'form_classname', None),
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
                    data.get('%s-%d-id' % (prefix, i)),
                )
            )

        values_with_indexes.sort()
        return StreamValue(self, [
            (child_block_type_name, value, block_id)
            for (index, child_block_type_name, value, block_id) in values_with_indexes
        ])

    def value_omitted_from_data(self, data, files, prefix):
        return ('%s-count' % prefix) not in data

    @property
    def required(self):
        return self.meta.required

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

    def bulk_to_python(self, values):
        # 'values' is a list of streams, each stream being a list of dicts with 'type', 'value' and
        # optionally 'id'.
        # We will iterate over these streams, constructing:
        # 1) a set of per-child-block lists ('child_inputs'), to be sent to each child block's
        #    bulk_to_python method in turn (giving us 'child_outputs')
        # 2) a 'block map' of each stream, telling us the type and id of each block and the index we
        #    need to look up in the corresponding child_outputs list to obtain its final value

        child_inputs = defaultdict(list)
        block_maps = []

        for stream in values:
            block_map = []
            for block_dict in stream:
                block_type = block_dict['type']

                if block_type not in self.child_blocks:
                    # skip any blocks with an unrecognised type
                    continue

                child_input_list = child_inputs[block_type]
                child_index = len(child_input_list)
                child_input_list.append(block_dict['value'])
                block_map.append(
                    (block_type, block_dict.get('id'), child_index)
                )

            block_maps.append(block_map)

        # run each list in child_inputs through the relevant block's bulk_to_python
        # to obtain child_outputs
        child_outputs = {
            block_type: self.child_blocks[block_type].bulk_to_python(child_input_list)
            for block_type, child_input_list in child_inputs.items()
        }

        # for each stream, go through the block map, picking out the appropriately-indexed
        # value from the relevant list in child_outputs
        return [
            StreamValue(
                self,
                [
                    (block_type, child_outputs[block_type][child_index], id)
                    for block_type, id, child_index in block_map
                ],
                is_lazy=False
            )
            for block_map in block_maps
        ]

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


class StreamValue(MutableSequence):
    """
    Custom type used to represent the value of a StreamBlock; behaves as a sequence of BoundBlocks
    (which keep track of block types in a way that the values alone wouldn't).
    """

    class StreamChild(BoundBlock):
        """
        Iterating over (or indexing into) a StreamValue returns instances of StreamChild.
        These are wrappers for the individual data items in the stream, extending BoundBlock
        (which keeps track of the data item's corresponding Block definition object, and provides
        the `render` method to render itself with a template) with an `id` property (a UUID
        assigned to the item - this is managed by the enclosing StreamBlock and is not a property
        of blocks in general) and a `block_type` property.
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

        def get_prep_value(self):
            return {
                'type': self.block_type,
                'value': self.block.get_prep_value(self.value),
                'id': self.id,
            }

        def _as_tuple(self):
            if self.id:
                return (self.block.name, self.value, self.id)
            else:
                return (self.block.name, self.value)

    class RawDataView(MutableSequence):
        """
        Internal helper class to present the stream data in raw JSONish format. For backwards
        compatibility with old code that manipulated StreamValue.stream_data, this is considered
        mutable to some extent, with the proviso that once the BoundBlock representation has been
        accessed, any changes to fields within raw data will not propagate back to the BoundBlock
        and will not be saved back when calling get_prep_value.
        """
        def __init__(self, stream_value):
            self.stream_value = stream_value

        def __getitem__(self, i):
            item = self.stream_value._raw_data[i]
            if item is None:
                # reconstruct raw data from the bound block
                item = self.stream_value._bound_blocks[i].get_prep_value()
                self.stream_value._raw_data[i] = item

            return item

        def __len__(self):
            return len(self.stream_value._raw_data)

        def __setitem__(self, i, item):
            self.stream_value._raw_data[i] = item
            # clear the cached bound_block for this item
            self.stream_value._bound_blocks[i] = None

        def __delitem__(self, i):
            # same as deletion on the stream itself - delete both the raw and bound_block data
            del self.stream_value[i]

        def insert(self, i, item):
            self.stream_value._raw_data.insert(i, item)
            self.stream_value._bound_blocks.insert(i, None)

        def __repr__(self):
            return repr(list(self))

    class TupleView(MutableSequence):
        """
        RemovedInWagtail214Warning:
        Internal helper class to replicate the old behaviour of StreamValue.stream_data on a
        non-lazy StreamValue. This only exists for backwards compatibility and can be dropped
        once stream_data has been retired.
        """
        def __init__(self, stream_value):
            self.stream_value = stream_value

        def __getitem__(self, i):
            # convert BoundBlock to tuple representation on retrieval
            return self.stream_value[i]._as_tuple()

        # all other methods can be proxied directly to StreamValue, since its assignment /
        # insertion methods accept the tuple representation

        def __len__(self):
            return len(self.stream_value)

        def __setitem__(self, i, item):
            self.stream_value[i] = item

        def __delitem__(self, i):
            del self.stream_value[i]

        def insert(self, i, item):
            self.stream_value.insert(i, item)

        def __repr__(self):
            return repr(list(self))

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
        self.stream_block = stream_block  # the StreamBlock object that handles this value
        self.is_lazy = is_lazy
        self.raw_text = raw_text

        if is_lazy:
            # store raw stream data in _raw_data; on retrieval it will be converted to a native
            # value (via block.to_python) and wrapped as a StreamValue, and cached in _bound_blocks.
            self._raw_data = stream_data
            self._bound_blocks = [None] * len(stream_data)
        else:
            # store native stream data in _bound_blocks; on serialization it will be converted to
            # a JSON-ish representation via block.get_prep_value.
            self._raw_data = [None] * len(stream_data)
            self._bound_blocks = [
                self._construct_stream_child(item) for item in stream_data
            ]

    def _construct_stream_child(self, item):
        """
        Create a StreamChild instance from a (type, value, id) or (type, value) tuple,
        or return item if it's already a StreamChild
        """
        if isinstance(item, StreamValue.StreamChild):
            return item

        try:
            type_name, value, block_id = item
        except ValueError:
            type_name, value = item
            block_id = None

        block_def = self.stream_block.child_blocks[type_name]
        return StreamValue.StreamChild(block_def, value, id=block_id)

    def __getitem__(self, i):
        if self._bound_blocks[i] is None:
            raw_value = self._raw_data[i]
            self._prefetch_blocks(raw_value['type'])

        return self._bound_blocks[i]

    def __setitem__(self, i, item):
        self._bound_blocks[i] = self._construct_stream_child(item)

    def __delitem__(self, i):
        del self._bound_blocks[i]
        del self._raw_data[i]

    def insert(self, i, item):
        self._bound_blocks.insert(i, self._construct_stream_child(item))
        self._raw_data.insert(i, None)

    @cached_property
    def raw_data(self):
        return StreamValue.RawDataView(self)

    @cached_property
    def stream_data(self):
        warnings.warn(
            "The stream_data property of StreamField / StreamBlock values is deprecated.\n"
            "HINT: Instead of value.stream_data[i], retrieve block objects with value[i] "
            "or access the raw JSON-like data via value.raw_data[i].",
            RemovedInWagtail214Warning
        )
        if self.is_lazy:
            return StreamValue.RawDataView(self)
        else:
            return StreamValue.TupleView(self)

    def _prefetch_blocks(self, type_name):
        """
        Populate _bound_blocks with all items in this stream of type `type_name` that exist in
        _raw_data but do not already exist in _bound_blocks.

        Fetching is done via the block's bulk_to_python method, so that database lookups are
        batched into a single query where possible.
        """
        child_block = self.stream_block.child_blocks[type_name]
        # create a mapping of all the child blocks matching the given block type,
        # mapping (index within the stream) => (raw block value)
        raw_values = OrderedDict(
            (i, raw_item['value']) for i, raw_item in enumerate(self._raw_data)
            if raw_item['type'] == type_name and self._bound_blocks[i] is None
        )
        # pass the raw block values to bulk_to_python as a list
        converted_values = child_block.bulk_to_python(raw_values.values())

        # reunite the converted values with their stream indexes, along with the block ID
        # if one exists
        for i, value in zip(raw_values.keys(), converted_values):
            self._bound_blocks[i] = StreamValue.StreamChild(
                child_block, value, id=self._raw_data[i].get('id')
            )

    def get_prep_value(self):
        prep_value = []

        for i, item in enumerate(self._bound_blocks):
            if item:
                # Convert the native value back into raw JSONish data
                if not item.id:
                    item.id = str(uuid.uuid4())

                prep_value.append(item.get_prep_value())
            else:
                # item has not been converted to a BoundBlock, so its _raw_data entry is
                # still usable (but ensure it has an ID before returning it)

                raw_item = self._raw_data[i]
                if not raw_item.get('id'):
                    raw_item['id'] = str(uuid.uuid4())

                prep_value.append(raw_item)

        return prep_value

    def __eq__(self, other):
        if not isinstance(other, StreamValue) or len(other) != len(self):
            return False

        # scan both lists for non-matching items
        for i in range(0, len(self)):
            if self._bound_blocks[i] is None and other._bound_blocks[i] is None:
                # compare raw values as a shortcut to save the conversion step
                if self._raw_data[i] != other._raw_data[i]:
                    return False
            else:
                this_item = self[i]
                other_item = other[i]
                if (
                    this_item.block_type != other_item.block_type
                    or this_item.id != other_item.id
                    or this_item.value != other_item.value
                ):
                    return False

        return True

    def __len__(self):
        return len(self._bound_blocks)

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, list(self))

    def render_as_block(self, context=None):
        return self.stream_block.render(self, context=context)

    def __html__(self):
        return self.stream_block.render(self)

    def __str__(self):
        return self.__html__()
