# Placeholder for panel types defined in wagtail.admin.panels.
# These are needed because we wish to define properties such as `content_panels` on core models
# such as Page, but importing from wagtail.admin would create a circular import. We therefore use a
# placeholder object, and swap it out for the real panel class inside
# `wagtail.admin.panels.model_utils.expand_panel_list` at the same time as converting strings to
# FieldPanel instances.

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.module_loading import import_string


class PanelPlaceholder:
    def __init__(self, path, args, kwargs):
        self.path = path
        self.args = args
        self.kwargs = kwargs

    @cached_property
    def panel_class(self):
        return import_string(self.path)

    def construct(self):
        return self.panel_class(*self.args, **self.kwargs)


class CommentPanelPlaceholder(PanelPlaceholder):
    def __init__(self):
        super().__init__(
            "wagtail.admin.panels.CommentPanel",
            [],
            {},
        )

    def construct(self):
        if getattr(settings, "WAGTAILADMIN_COMMENTS_ENABLED", True):
            return super().construct()
