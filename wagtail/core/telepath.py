from django import forms
from django.forms import MediaDefiningClass

from wagtail.admin.staticfiles import versioned_static


DICT_RESERVED_KEYS = ['_type', '_args', '_dict', '_list', '_val', '_id', '_ref']


class UnpackableTypeError(TypeError):
    pass


class Node:
    """
    Intermediate representation of a packed value. Subclasses represent a particular value
    type, and implement emit_verbose (returns a dict representation of a value that can have
    an _id attached) and emit_compact (returns a compact representation of the value, in any
    JSON-serialisable type).

    If this node is assigned an id, emit() will return the verbose representation with the
    id attached on first call, and a reference on subsequent calls.
    """
    def __init__(self):
        self.id = None
        self.seen = False

    def emit(self):
        if self.seen and self.id is not None:
            # Have already emitted this value, so emit a reference instead
            return {'_ref': self.id}
        else:
            self.seen = True
            if self.id is not None:
                # emit this value in long form including an ID
                result = self.emit_verbose()
                result['_id'] = self.id
                return result
            else:
                return self.emit_compact()


class ValueNode(Node):
    """Represents a primitive value; int, string etc"""
    def __init__(self, value):
        super().__init__()
        self.value = value

    def emit_verbose(self):
        return {'_val': self.value}

    def emit_compact(self):
        return self.value


class ListNode(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def emit_verbose(self):
        return {'_list': [item.emit() for item in self.value]}

    def emit_compact(self):
        return [item.emit() for item in self.value]


class DictNode(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def emit_verbose(self):
        return {'_dict': {key: val.emit() for key, val in self.value.items()}}

    def emit_compact(self):
        if any(reserved_key in self.value for reserved_key in DICT_RESERVED_KEYS):
            # compact representation is not valid as this dict contains reserved keys
            # that would clash with the verbose representation
            return self.emit_verbose()
        else:
            return {key: val.emit() for key, val in self.value.items()}


class ObjectNode(Node):
    def __init__(self, constructor, args):
        super().__init__()
        self.constructor = constructor
        self.args = args

    def emit_verbose(self):
        return {
            '_type': self.constructor,
            '_args': [arg.emit() for arg in self.args]
        }

    def emit_compact(self):
        # objects always use verbose representation
        return self.emit_verbose()


class BaseAdapter:
    """Handles serialisation of a specific object type"""
    def pack(self, obj, context):
        """
        Translates obj into serialisable form. Any media declarations that will be required for
        deserialisation of the object should be passed to context.add_media().

        This base implementation handles simple JSON-serialisable values such as strings, and
        returns them unchanged.
        """
        return ValueNode(obj)


class DictAdapter(BaseAdapter):
    """Handles serialisation of dicts"""
    def pack(self, obj, context):
        return DictNode({
            str(key): context.pack(val)
            for key, val in obj.items()
        })


class Adapter(BaseAdapter, metaclass=MediaDefiningClass):
    """
    Handles serialisation of custom types.
    Subclasses should define:
    - js_constructor: namespaced identifier for the JS constructor function that will unpack this
        object
    - js_args(obj): returns a list of (telepath-packable) arguments to be passed to the constructor
    - get_media(obj) or class Media: media definitions necessary for unpacking

    The adapter should then be registered with register(adapter, cls).
    """

    def get_media(self, obj):
        return self.media

    def pack(self, obj, context):
        context.add_media(self.get_media(obj))
        return ObjectNode(
            self.js_constructor,
            [context.pack(arg) for arg in self.js_args(obj)]
        )


adapters = {
    # Primitive value types that are unchanged on serialisation
    type(None): BaseAdapter(),
    bool: BaseAdapter(),
    int: BaseAdapter(),
    float: BaseAdapter(),
    str: BaseAdapter(),

    # Container types to be serialised recursively
    dict: DictAdapter(),
    # Iterable types (list, tuple, odict_values...) do not have a reliably recognisable
    # superclass, so will be handled as a special case
}


def register(adapter, cls):
    adapters[cls] = adapter


class JSContext:
    def __init__(self):
        self.media = forms.Media(js=[
            versioned_static('wagtailadmin/js/telepath/telepath.js')
        ])

        # Keep track of media declarations that have already added to self.media - ones that
        # exactly match a previous one can be ignored, as they will not affect the result
        self.media_fragments = set([str(self.media)])

    def add_media(self, media):
        media_str = str(media)
        if media_str not in self.media_fragments:
            self.media += media
            self.media_fragments.add(media_str)

    def pack(self, obj):
        return ValueContext(self).pack(obj).emit()


class ValueContext:
    """
    A context instantiated for each top-level value that JSContext.pack is called on.
    Values packed in this context will be kept in a lookup table; if over the course of
    packing the top level value we encounter multiple references to the same value, a
    reference to the previously-packed value will be generated rather than packing it
    again. Calls to add_media are passed back to the parent context so that multiple
    calls to pack() will have their media combined in a single bundle.
    """
    def __init__(self, parent_context):
        self.parent_context = parent_context
        self.packed_values = {}
        self.next_id = 0

    def add_media(self, media):
        self.parent_context.add_media(media)

    def pack(self, val):
        obj_id = id(val)
        try:
            existing_packed_val = self.packed_values[obj_id]
        except KeyError:
            # not seen this value before, so pack it and store in packed_values
            packed_val = self._pack_as_value(val)
            self.packed_values[obj_id] = packed_val
            return packed_val

        # Assign existing_packed_val an ID so that we can create references to it
        existing_packed_val.id = self.next_id
        self.next_id += 1
        return existing_packed_val

    def _pack_as_value(self, obj):
        for cls in type(obj).__mro__:
            adapter = adapters.get(cls)
            if adapter:
                return adapter.pack(obj, self)

        # as fallback, try handling as an iterable
        try:
            return ListNode([self.pack(item) for item in obj])
        except UnpackableTypeError:  # error while packing an item
            raise
        except TypeError:  # obj is not iterable
            pass

        raise UnpackableTypeError("don't know how to pack object: %r" % obj)
