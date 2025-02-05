import itertools
import json
import uuid
from collections import OrderedDict, defaultdict
from collections.abc import Mapping, MutableSequence
from pickle import PickleError

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.fields import _load_field
from django.forms.utils import ErrorList
from django.utils.functional import cached_property
from django.utils.html import format_html_join
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.telepath import Adapter, register

from .base import (
    Block,
    BoundBlock,
    DeclarativeSubBlocksMetaclass,
    get_error_json_data,
    get_error_list_json_data,
    get_help_icon,
)

__all__ = [
    "BaseStreamBlock",
    "StreamBlock",
    "StreamValue",
    "StreamBlockValidationError",
]


class StreamBlockValidationError(ValidationError):
    def __init__(self, block_errors=None, non_block_errors=None):
        # non_block_errors may be passed here as an ErrorList, a plain list (of strings or
        # ValidationErrors), or None.
        # Normalise it to be an ErrorList, which provides an as_data() method that consistently
        # returns a flat list of ValidationError objects.
        self.non_block_errors = ErrorList(non_block_errors)

        # block_errors may be passed here as None, or a dict keyed by the indexes of the child blocks
        # with errors.
        # Items in this list / dict may be:
        #  - a ValidationError instance (potentially a subclass such as StructBlockValidationError)
        #  - an ErrorList containing a single ValidationError
        #  - a plain list containing a single ValidationError
        # All representations will be normalised to a dict of ValidationError instances,
        # which is also the preferred format for the original argument to be in.
        self.block_errors = {}
        if block_errors is None:
            pass
        else:
            for index, val in block_errors.items():
                if isinstance(val, ErrorList):
                    self.block_errors[index] = val.as_data()[0]
                elif isinstance(val, list):
                    self.block_errors[index] = val[0]
                else:
                    self.block_errors[index] = val

        super().__init__("Validation error in StreamBlock")

    def as_json_data(self):
        result = {}
        if self.non_block_errors:
            result["messages"] = get_error_list_json_data(self.non_block_errors)
        if self.block_errors:
            result["blockErrors"] = {
                index: get_error_json_data(error)
                for (index, error) in self.block_errors.items()
            }
        return result


class BaseStreamBlock(Block):
    def __init__(self, local_blocks=None, search_index=True, **kwargs):
        self._constructor_kwargs = kwargs
        self.search_index = search_index

        super().__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self.child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

    @classmethod
    def construct_from_lookup(cls, lookup, child_blocks, **kwargs):
        if child_blocks:
            child_blocks = [
                (name, lookup.get_block(index)) for name, index in child_blocks
            ]
        return cls(child_blocks, **kwargs)

    def empty_value(self, raw_text=None):
        return StreamValue(self, [], raw_text=raw_text)

    def sorted_child_blocks(self):
        """Child blocks, sorted in to their groups."""
        return sorted(
            self.child_blocks.values(), key=lambda child_block: child_block.meta.group
        )

    def grouped_child_blocks(self):
        """
        The available child block types of this stream block, organised into groups according to
        their meta.group attribute.
        Returned as an iterable of (group_name, list_of_blocks) tuples
        """
        return itertools.groupby(
            self.sorted_child_blocks(), key=lambda child_block: child_block.meta.group
        )

    def value_from_datadict(self, data, files, prefix):
        count = int(data["%s-count" % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data["%s-%d-deleted" % (prefix, i)]:
                continue
            block_type_name = data["%s-%d-type" % (prefix, i)]
            try:
                child_block = self.child_blocks[block_type_name]
            except KeyError:
                continue

            values_with_indexes.append(
                (
                    int(data["%s-%d-order" % (prefix, i)]),
                    block_type_name,
                    child_block.value_from_datadict(
                        data, files, "%s-%d-value" % (prefix, i)
                    ),
                    data.get("%s-%d-id" % (prefix, i)),
                )
            )

        values_with_indexes.sort()
        return StreamValue(
            self,
            [
                (child_block_type_name, value, block_id)
                for (
                    index,
                    child_block_type_name,
                    value,
                    block_id,
                ) in values_with_indexes
            ],
        )

    def value_omitted_from_data(self, data, files, prefix):
        return ("%s-count" % prefix) not in data

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
                errors[i] = e

        if self.meta.min_num is not None and self.meta.min_num > len(value):
            non_block_errors.append(
                ValidationError(
                    _("The minimum number of items is %(min_num)d")
                    % {"min_num": self.meta.min_num}
                )
            )
        elif self.required and len(value) == 0:
            non_block_errors.append(ValidationError(_("This field is required.")))

        if self.meta.max_num is not None and self.meta.max_num < len(value):
            non_block_errors.append(
                ValidationError(
                    _("The maximum number of items is %(max_num)d")
                    % {"max_num": self.meta.max_num}
                )
            )

        if self.meta.block_counts:
            block_counts = defaultdict(int)
            for item in value:
                block_counts[item.block_type] += 1

            for block_name, min_max in self.meta.block_counts.items():
                block = self.child_blocks[block_name]
                max_num = min_max.get("max_num", None)
                min_num = min_max.get("min_num", None)
                block_count = block_counts[block_name]
                if min_num is not None and min_num > block_count:
                    non_block_errors.append(
                        ValidationError(
                            "{}: {}".format(
                                block.label,
                                _("The minimum number of items is %(min_num)d")
                                % {"min_num": min_num},
                            )
                        )
                    )
                if max_num is not None and max_num < block_count:
                    non_block_errors.append(
                        ValidationError(
                            "{}: {}".format(
                                block.label,
                                _("The maximum number of items is %(max_num)d")
                                % {"max_num": max_num},
                            )
                        )
                    )

        if errors or non_block_errors:
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' list
            raise StreamBlockValidationError(
                block_errors=errors, non_block_errors=non_block_errors
            )

        return StreamValue(self, cleaned_data)

    def to_python(self, value):
        if isinstance(value, StreamValue):
            return value
        elif isinstance(value, str) and value:
            try:
                value = json.loads(value)
            except ValueError:
                # value is not valid JSON; most likely, this field was previously a
                # rich text field before being migrated to StreamField, and the data
                # was left intact in the migration. Return an empty stream instead
                # (but keep the raw text available as an attribute, so that it can be
                # used to migrate that data to StreamField)
                return self.empty_value(raw_text=value)

        if not value:
            return self.empty_value()

        # ensure value is a list and not some other kind of iterable
        value = list(value)

        if isinstance(value[0], dict):
            # value is in JSONish representation - a dict with 'type' and 'value' keys.
            # This is passed to StreamValue to be expanded lazily - but first we reject any unrecognised
            # block types from the list
            return StreamValue(
                self,
                [
                    child_data
                    for child_data in value
                    if child_data["type"] in self.child_blocks
                ],
                is_lazy=True,
            )
        else:
            # See if it looks like the standard non-smart representation of a
            # StreamField value: a list of (block_name, value) tuples
            try:
                [None for (x, y) in value]
            except (TypeError, ValueError) as exc:
                # Give up trying to make sense of the value
                raise TypeError(
                    f"Cannot handle {value!r} (type {type(value)!r}) as a value of a StreamBlock"
                ) from exc

            # Test succeeded, so return as a StreamValue-ified version of that value
            return StreamValue(
                self,
                [
                    (k, self.child_blocks[k].normalize(v))
                    for k, v in value
                    if k in self.child_blocks
                ],
            )

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
                block_type = block_dict["type"]

                if block_type not in self.child_blocks:
                    # skip any blocks with an unrecognised type
                    continue

                child_input_list = child_inputs[block_type]
                child_index = len(child_input_list)
                child_input_list.append(block_dict["value"])
                block_map.append((block_type, block_dict.get("id"), child_index))

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
                is_lazy=False,
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

    def normalize(self, value):
        return self.to_python(value)

    def get_form_state(self, value):
        if not value:
            return []
        else:
            return [
                {
                    "type": child.block.name,
                    "value": child.block.get_form_state(child.value),
                    "id": child.id,
                }
                for child in value
            ]

    def get_api_representation(self, value, context=None):
        if value is None:
            # treat None as identical to an empty stream
            return []

        return [
            {
                "type": child.block.name,
                "value": child.block.get_api_representation(
                    child.value, context=context
                ),
                "id": child.id,
            }
            for child in value  # child is a StreamChild instance
        ]

    def render_basic(self, value, context=None):
        return format_html_join(
            "\n",
            '<div class="block-{1}">{0}</div>',
            [(child.render(context=context), child.block_type) for child in value],
        )

    def get_searchable_content(self, value):
        if not self.search_index:
            return []
        content = []

        for child in value:
            content.extend(child.block.get_searchable_content(child.value))

        return content

    def extract_references(self, value):
        for child in value:
            for (
                model,
                object_id,
                model_path,
                content_path,
            ) in child.block.extract_references(child.value):
                model_path = (
                    f"{child.block_type}.{model_path}"
                    if model_path
                    else child.block_type
                )
                content_path = (
                    f"{child.id}.{content_path}" if content_path else child.id
                )
                yield model, object_id, model_path, content_path

    def get_block_by_content_path(self, value, path_elements):
        """
        Given a list of elements from a content path, retrieve the block at that path
        as a BoundBlock object, or None if the path does not correspond to a valid block.
        """
        if path_elements:
            id, *remaining_elements = path_elements
            for child in value:
                if child.id == id:
                    return child.block.get_block_by_content_path(
                        child.value, remaining_elements
                    )
        else:
            # an empty path refers to the stream as a whole
            return self.bind(value)

    def deconstruct(self):
        """
        Always deconstruct StreamBlock instances as if they were plain StreamBlocks with all of the
        field definitions passed to the constructor - even if in reality this is a subclass of StreamBlock
        with the fields defined declaratively, or some combination of the two.

        This ensures that the field definitions get frozen into migrations, rather than leaving a reference
        to a custom subclass in the user's models.py that may or may not stick around.
        """
        path = "wagtail.blocks.StreamBlock"
        args = [list(self.child_blocks.items())]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def deconstruct_with_lookup(self, lookup):
        path = "wagtail.blocks.StreamBlock"
        args = [
            [
                (name, lookup.add_block(block))
                for name, block in self.child_blocks.items()
            ]
        ]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    @cached_property
    def _has_default(self):
        return self.meta.default is not BaseStreamBlock._meta_class.default

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"
        default = []
        required = True
        form_classname = None
        min_num = None
        max_num = None
        block_counts = {}
        collapsed = False

    MUTABLE_META_ATTRIBUTES = [
        "required",
        "min_num",
        "max_num",
        "block_counts",
        "collapsed",
    ]


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
            self.id = kwargs.pop("id")
            super().__init__(*args, **kwargs)

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
                "type": self.block_type,
                "value": self.block.get_prep_value(self.value),
                "id": self.id,
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

    class BlockNameLookup(Mapping):
        """
        Dict-like object returned from `blocks_by_name`, for looking up a stream's blocks by name.
        Uses lazy evaluation on access, so that we're not redundantly constructing StreamChild
        instances for blocks of different names.
        """

        def __init__(self, stream_value, find_all=True):
            self.stream_value = stream_value
            self.block_names = stream_value.stream_block.child_blocks.keys()
            self.find_all = (
                find_all  # whether to return all results rather than just the first
            )

        def __getitem__(self, block_name):
            result = [] if self.find_all else None

            if block_name not in self.block_names:
                # skip the search and return an empty result
                return result

            for i in range(len(self.stream_value)):
                # Skip over blocks that have not yet been instantiated from _raw_data and are of
                # different names to the one we're looking for
                if (
                    self.stream_value._bound_blocks[i] is None
                    and self.stream_value._raw_data[i]["type"] != block_name
                ):
                    continue

                block = self.stream_value[i]
                if block.block_type == block_name:
                    if self.find_all:
                        result.append(block)
                    else:
                        return block

            return result

        def __iter__(self):
            yield from self.block_names

        def __len__(self):
            return len(self.block_names)

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
        self.stream_block = (
            stream_block  # the StreamBlock object that handles this value
        )
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
        if isinstance(i, slice):
            start, stop, step = i.indices(len(self._bound_blocks))
            return [self[j] for j in range(start, stop, step)]

        if self._bound_blocks[i] is None:
            raw_value = self._raw_data[i]
            self._prefetch_blocks(raw_value["type"])

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
            (i, raw_item["value"])
            for i, raw_item in enumerate(self._raw_data)
            if self._bound_blocks[i] is None and raw_item["type"] == type_name
        )
        # pass the raw block values to bulk_to_python as a list
        converted_values = child_block.bulk_to_python(raw_values.values())

        # reunite the converted values with their stream indexes, along with the block ID
        # if one exists
        for i, value in zip(raw_values.keys(), converted_values):
            self._bound_blocks[i] = StreamValue.StreamChild(
                child_block, value, id=self._raw_data[i].get("id")
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
                if not raw_item.get("id"):
                    raw_item["id"] = str(uuid.uuid4())

                prep_value.append(raw_item)

        return prep_value

    def blocks_by_name(self, block_name=None):
        lookup = StreamValue.BlockNameLookup(self, find_all=True)
        if block_name:
            return lookup[block_name]
        else:
            return lookup

    def first_block_by_name(self, block_name=None):
        lookup = StreamValue.BlockNameLookup(self, find_all=False)
        if block_name:
            return lookup[block_name]
        else:
            return lookup

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
        return f"<{type(self).__name__} {list(self)!r}>"

    def render_as_block(self, context=None):
        return self.stream_block.render(self, context=context)

    def __html__(self):
        return self.stream_block.render(self)

    def __str__(self):
        return self.__html__()

    @staticmethod
    def _deserialize_pickle_value(app_label, model_name, field_name, field_value):
        """Returns StreamValue from pickled data"""
        field = _load_field(app_label, model_name, field_name)
        return field.to_python(field_value)

    def __reduce__(self):
        try:
            stream_field = self._stream_field
        except AttributeError:
            raise PickleError(
                "StreamValue can only be pickled if it is associated with a StreamField"
            )

        return (
            self._deserialize_pickle_value,
            (
                stream_field.model._meta.app_label,
                stream_field.model._meta.object_name,
                stream_field.name,
                self.get_prep_value(),
            ),
        )


class StreamBlockAdapter(Adapter):
    js_constructor = "wagtail.blocks.StreamBlock"

    def js_args(self, block):
        meta = {
            "label": block.label,
            "description": block.get_description(),
            "required": block.required,
            "icon": block.meta.icon,
            "blockDefId": block.definition_prefix,
            "isPreviewable": block.is_previewable,
            "classname": block.meta.form_classname,
            "maxNum": block.meta.max_num,
            "minNum": block.meta.min_num,
            "blockCounts": block.meta.block_counts,
            "collapsed": block.meta.collapsed,
            "strings": {
                "MOVE_UP": _("Move up"),
                "MOVE_DOWN": _("Move down"),
                "DRAG": _("Drag"),
                "DUPLICATE": _("Duplicate"),
                "DELETE": _("Delete"),
                "ADD": _("Add"),
            },
        }
        help_text = getattr(block.meta, "help_text", None)
        if help_text:
            meta["helpText"] = help_text
            meta["helpIcon"] = get_help_icon()

        return [
            block.name,
            block.grouped_child_blocks(),
            {
                name: child_block.get_form_state(child_block.get_default())
                for name, child_block in block.child_blocks.items()
            },
            meta,
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/telepath/blocks.js"),
            ]
        )


register(StreamBlockAdapter(), StreamBlock)
