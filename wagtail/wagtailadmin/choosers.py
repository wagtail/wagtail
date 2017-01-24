from __future__ import absolute_import, unicode_literals


class ChooserRegistry(object):
    def __init__(self):
        self._default_widget = None
        self._widgets = {}

    def register_default_widget(self, widget_cls):
        self._default_widget = widget_cls

    def register_widget(self, model, widget_cls):
        self._widgets[model] = widget_cls

    def get_widget(self, model):
        # TODO check parent models
        return self._widgets.get(model, self._default_widget)


choosers = ChooserRegistry()
