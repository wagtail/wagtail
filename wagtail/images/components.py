from wagtail.admin.ui.fields import BaseFieldDisplay
from wagtail.images.shortcuts import get_rendition_or_not_found


class ImageDisplay(BaseFieldDisplay):
    rendition_spec = "max-400x400"

    def render_html(self, parent_context):
        if self.value is None:
            return None
        return get_rendition_or_not_found(self.value, self.rendition_spec).img_tag()
