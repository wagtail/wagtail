import json

from wagtail.wagtailcore.fields import BaseRichTextEditor


class HalloEditor(BaseRichTextEditor):

    def render_js_init(self, id_, name, value):
        return "makeHalloEditable({0});".format(json.dumps(id_))
