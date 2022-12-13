from django.forms import Media

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets.datetime import AdminDateTimeInput
from wagtail.models import Page

from .field_panel import FieldPanel
from .group import FieldRowPanel, MultiFieldPanel


# This allows users to include the publishing panel in their own per-model override
# without having to write these fields out by hand, potentially losing 'classname'
# and therefore the associated styling of the publishing panel
class PublishingPanel(MultiFieldPanel):
    def __init__(self, **kwargs):
        js_overlay_parent_selector = "#schedule-publishing-dialog"
        updated_kwargs = {
            "children": [
                FieldRowPanel(
                    [
                        FieldPanel(
                            "go_live_at",
                            widget=AdminDateTimeInput(
                                js_overlay_parent_selector=js_overlay_parent_selector,
                            ),
                        ),
                        FieldPanel(
                            "expire_at",
                            widget=AdminDateTimeInput(
                                js_overlay_parent_selector=js_overlay_parent_selector,
                            ),
                        ),
                    ],
                ),
            ],
            "classname": "publishing",
        }
        updated_kwargs.update(kwargs)
        super().__init__(**updated_kwargs)

    @property
    def clean_name(self):
        return super().clean_name or "publishing"

    class BoundPanel(MultiFieldPanel.BoundPanel):
        template_name = "wagtailadmin/panels/publishing/schedule_publishing_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["request"] = self.request
            context["instance"] = self.instance
            context["classname"] = self.classname
            if isinstance(self.instance, Page):
                context["page"] = self.instance
            return context

        def show_panel_furniture(self):
            return False

        @property
        def media(self):
            return super().media + Media(
                js=[versioned_static("wagtailadmin/js/schedule-publishing.js")],
            )
