from __future__ import absolute_import, unicode_literals

import json

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminDocumentChooser(AdminChooser):
    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))
