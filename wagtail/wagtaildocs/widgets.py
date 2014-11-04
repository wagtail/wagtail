from __future__ import absolute_import, unicode_literals

import json

from django.forms import widgets

from wagtail.utils.widgets import WidgetWithScript


class AdminDocumentChooser(WidgetWithScript, widgets.Input):
    input_type = 'hidden'

    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))
