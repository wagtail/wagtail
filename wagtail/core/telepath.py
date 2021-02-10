from django import forms
from telepath import Adapter, AdapterRegistry, JSContextBase  # noqa

from wagtail.admin.staticfiles import versioned_static


class WagtailJSContextBase(JSContextBase):
    @property
    def base_media(self):
        return forms.Media(js=[
            versioned_static(self.telepath_js_path),
        ])


class WagtailAdapterRegistry(AdapterRegistry):
    js_context_base_class = WagtailJSContextBase


registry = WagtailAdapterRegistry(telepath_js_path='wagtailadmin/js/telepath/telepath.js')
JSContext = registry.js_context_class


def register(adapter, cls):
    registry.register(adapter, cls)
