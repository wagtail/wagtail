from wagtail.admin.ui.side_panels import (
    BaseSidePanels,
    BaseStatusSidePanel,
    PreviewSidePanel,
)
from wagtail.models import PreviewableMixin


class SnippetSidePanels(BaseSidePanels):
    def __init__(
        self,
        request,
        object,
        view,
        *,
        show_schedule_publishing_toggle,
        live_object=None,
        scheduled_object=None,
    ):
        self.side_panels = []
        if object.pk or view.locale or show_schedule_publishing_toggle:
            self.side_panels += [
                BaseStatusSidePanel(
                    object,
                    request,
                    show_schedule_publishing_toggle=show_schedule_publishing_toggle,
                    live_object=live_object,
                    scheduled_object=scheduled_object,
                ),
            ]

        if isinstance(object, PreviewableMixin) and object.is_previewable():
            self.side_panels += [
                PreviewSidePanel(object, request),
            ]
