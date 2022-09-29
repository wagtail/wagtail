from warnings import warn

from wagtail.admin.panels import FieldPanel
from wagtail.utils.deprecation import RemovedInWagtail50Warning


class SnippetChooserPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "SnippetChooserPanel is no longer required for snippet choosers, and should be replaced by FieldPanel. "
            "SnippetChooserPanel will be removed in a future release. "
            "See https://docs.wagtail.org/en/stable/releases/3.0.html#removal-of-special-purpose-field-panel-types",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
