from django import forms
from telepath import Adapter, AdapterRegistry, JSContextBase, ValueContext


class CyclePlaceholder:
    """
    Backport of: https://github.com/wagtail/telepath/pull/15

    Can be removed once that's merged.
    """

    def __init__(self):
        self.id = None
        self.seen = False
        self.use_id = True

    def emit(self):
        return {"_ref": self.id}


class WagtailValueContext(ValueContext):
    """
    Backport of: https://github.com/wagtail/telepath/pull/15

    Can be removed once that's merged.
    """

    def build_node(self, val):
        obj_id = id(val)
        if obj_id in self.nodes:
            existing_node = self.nodes[obj_id]
            if existing_node.id is None:
                existing_node.id = self.next_id
                self.next_id += 1
            return existing_node

        placeholder = CyclePlaceholder()
        self.nodes[obj_id] = placeholder
        self.raw_values[obj_id] = val

        node = self._build_new_node(val)

        if placeholder.id is not None:
            node.id = placeholder.id

        self.nodes[obj_id] = node
        return node


class WagtailJSContextBase(JSContextBase):
    def pack(self, obj):
        return WagtailValueContext(self).build_node(obj).emit()

    @property
    def base_media(self):
        # Do not include the telepath.js file in the base media, as it is already included
        # globally in admin_base.html.
        return forms.Media()


class WagtailAdapterRegistry(AdapterRegistry):
    js_context_base_class = WagtailJSContextBase


registry = WagtailAdapterRegistry(telepath_js_path=None)
JSContext = registry.js_context_class


def register(*args, **kwargs):
    return registry.register(*args, **kwargs)


def adapter(js_constructor, base=Adapter):
    """
    Allows a class to implement its adapting logic with a `js_args()` method on the class itself.
    This just helps reduce the amount of code you have to write.

    For example:

        @adapter('wagtail.mywidget')
        class MyWidget():
            ...

            def js_args(self):
                return [
                    self.foo,
                ]

    Is equivalent to:

        class MyWidget():
            ...


        class MyWidgetAdapter(Adapter):
            js_constructor = 'wagtail.mywidget'

            def js_args(self, obj):
                return [
                    self.foo,
                ]
    """

    def _wrapper(cls):
        ClassAdapter = type(
            cls.__name__ + "Adapter",
            (base,),
            {
                "js_constructor": js_constructor,
                "js_args": lambda self, obj: obj.js_args(),
            },
        )

        register(ClassAdapter(), cls)

        return cls

    return _wrapper
