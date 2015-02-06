from __future__ import absolute_import, unicode_literals

import json

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminSnippetChooser(AdminChooser):
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        super(AdminSnippetChooser, self).__init__(**kwargs)
        if content_type is not None:
            self.target_content_type = content_type

    def render_js_init(self, id_, name, value):
        content_type = self.target_content_type

        return "createSnippetChooser({id}, {content_type});".format(
            id=json.dumps(id_),
            content_type=json.dumps('{app}/{model}'.format(
                app=content_type.app_label,
                model=content_type.model)))
