from warnings import warn

from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .base import Panel
from .field_panel import FieldPanel
from .group import PanelGroup


class EditHandler(Panel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.EditHandler has been renamed to wagtail.admin.panels.Panel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class BaseCompositeEditHandler(PanelGroup):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.BaseCompositeEditHandler has been renamed to wagtail.admin.panels.PanelGroup",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class RichTextFieldPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "RichTextFieldPanel is no longer required for rich text fields, and should be replaced by FieldPanel. "
            "RichTextFieldPanel will be removed in a future release. "
            "See https://docs.wagtail.org/en/stable/releases/3.0.html#removal-of-special-purpose-field-panel-types",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class BaseChooserPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.BaseChooserPanel is obsolete and should be replaced by wagtail.admin.panels.FieldPanel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class StreamFieldPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "StreamFieldPanel is no longer required when using StreamField, and should be replaced by FieldPanel. "
            "StreamFieldPanel will be removed in a future release. "
            "See https://docs.wagtail.org/en/stable/releases/3.0.html#removal-of-special-purpose-field-panel-types",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
