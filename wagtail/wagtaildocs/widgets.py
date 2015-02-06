from __future__ import absolute_import, unicode_literals

import json

from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminDocumentChooser(AdminChooser):
    choose_one_text = _('Choose a document')
    choose_another_text = _('Choose another document')

    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))
