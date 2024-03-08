from django import forms
from django.forms import MediaDefiningClass
from django.utils.functional import cached_property, Promise


DICT_RESERVED_KEYS = ['_type', '_args', '_dict', '_list', '_val', '_id', '_ref']
STRING_REF_MIN_LENGTH = 20  # do not turn strings shorter than this into references


class UnpackableTypeError(TypeError):
    pass


class Node:
    """
    Intermediate representation of a packed value. Subclasses represent a particular value
    type, and implement emit_verbose (returns a dict representation of a value that can have
    an _id attached) and emit_compact (returns a compact representation of the value, in any
    JSON-serialisable type).

    If this node is assigned an id, emit() will return the verbose representation with the
    id attached on first call, and a reference on subsequent calls. To disable this behaviour
    (e.g. for small primitive values where the reference representation adds unwanted overhead),
    set self.use_id = False.
    """
    def __init__(self):
        self.id = None
        self.seen = False
        self.use_id = True

    def emit(self):
        if self.use_id and self.seen and self.id is not None:
            # Have already emitted this value, so emit a reference instead
            return {'_ref': self.id}
        else:
            self.seen = True
            if self.use_id and self.id is not None:
                # emit this value in long form including an ID
                result = self.emit_verbose()
                result['_id'] = self.id
                return result
            else:
                return self.emit_compact()


class ValueNode(Node):
    """Represents a primitive value; int, bool etc"""
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.use_id = False

    def emit_verbose(self):
        return {'_val': self.value}

    def emit_compact(self):
        return self.value


class StringNode(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.use_id = len(value) >= STRING_REF_MIN_LENGTH

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
    def build_node(self, obj, context):
        """
        Translates obj into a node that we can call emit() on to obtain the final serialisable
        form. Any media declarations that will be required for deserialisation of the object should
        be passed to context.add_media().

        This base implementation handles simple JSON-serialisable values such as integers, and
        wraps them as a ValueNode.
        """
        return ValueNode(obj)


class StringAdapter(BaseAdapter):
    def build_node(self, obj, context):
        return StringNode(obj)


class DictAdapter(BaseAdapter):
    """Handles serialisation of dicts"""
    def build_node(self, obj, context):
        return DictNode({
            str(key): context.build_node(val)
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
        return (self.js_constructor, self.js_args(obj))

    def build_node(self, obj, context):
        constructor, args = self.pack(obj, context)
        return ObjectNode(
            constructor, [context.build_node(arg) for arg in args]
        )


class AutoAdapter(Adapter):
    """
    Adapter for objects that define their own telepath_pack method that we can simply delegate to.
    """
    def pack(self, obj, context):
        return obj.telepath_pack(context)


class JSContextBase:
    """
    Base class for JSContext classes obtained through AdapterRegistry.js_context_class.
    Subclasses of this are assigned the following class attributes:
    registry - points to the associated AdapterRegistry
    telepath_js_path - path to telepath.js (as per standard Django staticfiles conventions)

    A JSContext handles packing a set of values to be used in the same request; calls to
    JSContext.pack will return the packed representation and also update the JSContext's media
    property to include all JS needed to unpack the values seen so far.
    """
    def __init__(self):
        self.media = self.base_media

        # Keep track of media declarations that have already added to self.media - ones that
        # exactly match a previous one can be ignored, as they will not affect the result
        self.media_fragments = set([str(self.media)])

    @property
    def base_media(self):
        return forms.Media(js=[self.telepath_js_path])

    def add_media(self, media=None, js=None, css=None):
        media_objects = []
        if media:
            media_objects.append(media)
        if js or css:
            if isinstance(js, str):
                # allow passing a single JS file name as equivalent to a singleton list
                js = [js]
            media_objects.append(forms.Media(js=js, css=css))

        for media_obj in media_objects:
            media_str = str(media_obj)
            if media_str not in self.media_fragments:
                self.media += media_obj
                self.media_fragments.add(media_str)

    def pack(self, obj):
        return ValueContext(self).build_node(obj).emit()


class AdapterRegistry:
    """
    Manages the mapping of Python types to their corresponding adapter implementations.
    """
    js_context_base_class = JSContextBase

    def __init__(self, telepath_js_path='telepath/js/telepath.js'):
        self.telepath_js_path = telepath_js_path
        self.adapters = {
            # Primitive value types that are unchanged on serialisation
            type(None): BaseAdapter(),
            bool: BaseAdapter(),
            int: BaseAdapter(),
            float: BaseAdapter(),
            str: StringAdapter(),

            # Container types to be serialised recursively
            dict: DictAdapter(),
            # Iterable types (list, tuple, odict_values...) do not have a reliably recognisable
            # superclass, so will be handled as a special case
        }

    def register(self, *args, **kwargs):
        if len(args) == 2 and not kwargs:
            # called as register(adapter, cls)
            adapter, cls = args
            if not isinstance(adapter, BaseAdapter):
                raise TypeError("register expected a BaseAdapter instance, got %r" % adapter)

            self.adapters[cls] = adapter

        elif not args:
            # called as a class decorator: @register() or @register(adapter=MyAdapter()) -
            # the return value here is the function that will receive the class definition
            adapter = kwargs.get('adapter') or AutoAdapter()
            if not isinstance(adapter, BaseAdapter):
                raise TypeError("register expected a BaseAdapter instance, got %r" % adapter)

            def wrapper(cls):
                # register the class and return it unchanged
                self.adapters[cls] = adapter
                return cls

            return wrapper

        elif len(args) == 1 and isinstance(args[0], type):
            # called as a class decorator @register without parentheses -
            # we are passed the class definition here
            cls = args[0]
            self.adapters[cls] = AutoAdapter()
            return cls

        else:
            raise TypeError(
                "register must be called as register(adapter, cls) or as a class decorator - "
                "@register or @register(adapter=MyAdapter())"
            )


    def find_adapter(self, cls):
        for base in cls.__mro__:
            adapter = self.adapters.get(base)
            if adapter is not None:
                return adapter

    @cached_property
    def js_context_class(self):
        return type('JSContext', (self.js_context_base_class,), {
            'registry': self,
            'telepath_js_path': self.telepath_js_path
        })


class ValueContext:
    """
    A context instantiated for each top-level value that JSContext.pack is called on. Results from
    this context's build_node method will be kept in a lookup table. If, over the course of
    building the node tree for the top level value, we encounter multiple references to the same
    value, a reference to the existing node will be generated rather than building it again. Calls
    to add_media are passed back to the parent context so that multiple calls to pack() will have
    their media combined in a single bundle.
    """
    def __init__(self, parent_context):
        self.parent_context = parent_context
        self.registry = parent_context.registry
        self.raw_values = {}
        self.nodes = {}
        self.next_id = 0

    def add_media(self, *args, **kwargs):
        self.parent_context.add_media(*args, **kwargs)

    def build_node(self, val):
        obj_id = id(val)
        try:
            existing_node = self.nodes[obj_id]
        except KeyError:
            # not seen this value before, so build a new node for it and store in self.nodes
            node = self._build_new_node(val)
            self.nodes[obj_id] = node
            # Also keep a reference to the original value to stop it from getting deallocated
            # and the ID being recycled
            self.raw_values[obj_id] = val

            return node

        if existing_node.id is None:
            # Assign existing_node an ID so that we can create references to it
            existing_node.id = self.next_id
            self.next_id += 1

        return existing_node

    def _build_new_node(self, obj):
        adapter = self.registry.find_adapter(type(obj))
        if adapter:
            return adapter.build_node(obj, self)

        # No adapter found; try special-case fallbacks

        if isinstance(obj, Promise):
            # object is a lazy object (e.g. gettext_lazy result);
            # handle as a string, translated to the currently active locale
            return StringNode(str(obj))

        # try handling as an iterable
        try:
            items = iter(obj)
        except TypeError:  # obj is not iterable
            raise UnpackableTypeError("don't know how to pack object: %r" % obj)
        else:
            return ListNode([self.build_node(item) for item in items])


# define a default registry of adapters. Typically this will be the only instance of
# AdapterRegistry in use, although packages may define their own 'private' registry if they
# have a set of adapters customised for their own use (e.g. with a custom JS path).

registry = AdapterRegistry()
JSContext = registry.js_context_class
register = registry.register
