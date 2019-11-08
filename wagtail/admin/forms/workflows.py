from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Workflow


class AdminWorkflow(Workflow):
    class Meta:
        proxy = True

    content_panels = [
        FieldPanel("name"),
        InlinePanel("workflow_tasks"),
    ]
