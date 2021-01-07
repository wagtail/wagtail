from django import forms
from django.forms import MediaDefiningClass

from wagtail.admin.staticfiles import versioned_static


adapters = {}


def register(adapter, cls):
    adapters[cls] = adapter


class JSContext:
    def __init__(self):
        self.media = forms.Media(js=[
            versioned_static('wagtailadmin/js/telepath/telepath.js')
        ])
        self.objects = {}

    def pack(self, obj):
        for cls in type(obj).__mro__:
            adapter = adapters.get(cls)
            if adapter:
                break

        if adapter is None:
            raise Exception("don't know how to add object to JS context: %r" % obj)

        self.media += adapter.get_media(obj, self)
        return [adapter.js_constructor, *adapter.js_args(obj, self)]


class Adapter(metaclass=MediaDefiningClass):
    def get_media(self, obj, context):
        return self.media
