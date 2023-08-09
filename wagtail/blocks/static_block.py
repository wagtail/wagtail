from django import forms
from django.utils.functional import cached_property
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.telepath import Adapter, register

from .base import Block

__all__ = ["StaticBlock"]


class StaticBlock(Block):
    """
    A block that just 'exists' and has no fields.
    """

    def get_admin_text(self):
        if self.meta.admin_text is None:
            if self.label:
                return _("%(label)s: this block has no options.") % {
                    "label": self.label
                }
            else:
                return _("This block has no options.")

        return self.meta.admin_text

    def value_from_datadict(self, data, files, prefix):
        return None

    class Meta:
        admin_text = None
        default = None


class StaticBlockAdapter(Adapter):
    js_constructor = "wagtail.blocks.StaticBlock"

    def js_args(self, block):
        admin_text = block.get_admin_text()

        if isinstance(admin_text, SafeString):
            text_or_html = "html"
        else:
            text_or_html = "text"

        return [
            block.name,
            {
                text_or_html: admin_text,
                "icon": block.meta.icon,
                "label": block.label,
            },
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/telepath/blocks.js"),
            ]
        )


register(StaticBlockAdapter(), StaticBlock)
