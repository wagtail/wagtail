from django import forms
from django.forms import MediaDefiningClass

from wagtail.admin.staticfiles import versioned_static


DICT_RESERVED_KEYS = ['_type', '_args', '_dict']


class UnpackableTypeError(TypeError):
    pass


class BaseAdapter:
    """Handles serialisation of a specific object type"""
    def pack(self, obj, context):
        """
        Translates obj into serialisable form. Any media declarations that will be required for
        deserialisation of the object should be passed to context.add_media().

        This base implementation handles simple JSON-serialisable values such as strings, and
        returns them unchanged.
        """
        return obj


class DictAdapter(BaseAdapter):
    """Handles serialisation of dicts"""
    def pack(self, obj, context):
        packed_obj = {
            str(key): context.pack(val)
            for key, val in obj.items()
        }
        if any(reserved_key in packed_obj for reserved_key in DICT_RESERVED_KEYS):
            # this dict contains keys such as _type that would collide with our object notation,
            # so wrap it in an explicit _dict to disambiguate
            return {'_dict': packed_obj}
        else:
            return packed_obj


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
        return {
            '_type': self.js_constructor,
            '_args': [context.pack(arg) for arg in self.js_args(obj)]
        }


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
        for cls in type(obj).__mro__:
            adapter = adapters.get(cls)
            if adapter:
                return adapter.pack(obj, self)

        # as fallback, try handling as an iterable
        try:
            return [self.pack(item) for item in obj]
        except UnpackableTypeError:  # error while packing an item
            raise
        except TypeError:  # obj is not iterable
            pass

        raise UnpackableTypeError("don't know how to pack object: %r" % obj)
