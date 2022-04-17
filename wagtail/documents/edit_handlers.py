from warnings import warn

from wagtail.admin.panels import FieldPanel
from wagtail.utils.deprecation import RemovedInWagtail50Warning


class DocumentChooserPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.documents.edit_handlers.DocumentChooserPanel is obsolete and should be replaced by wagtail.admin.panels.FieldPanel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
