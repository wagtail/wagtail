from __future__ import absolute_import, unicode_literals

import json

from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminImageChooser(AdminChooser):
    choose_one_text = _('Choose an image')
    choose_another_text = _('Choose another image')
    clear_choice_text = _('Clear image')

    def render_js_init(self, id_, name, value):
        return "createImageChooser({0});".format(json.dumps(id_))
