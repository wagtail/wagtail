from __future__ import absolute_import, unicode_literals

import json

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminImageChooser(AdminChooser):
    def render_js_init(self, id_, name, value):
        return "createImageChooser({0});".format(json.dumps(id_))
