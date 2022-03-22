from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin.panels import Panel


class FormSubmissionsPanel(Panel):
    template = "wagtailforms/panels/form_responses_panel.html"

    def on_model_bound(self):
        if not self.heading:
            self.heading = _("%s submissions") % self.model.get_verbose_name()

    class BoundPanel(Panel.BoundPanel):
        def render_html(self):
            form_page_model = self.panel.model
            form_submissions_model = form_page_model().get_submission_class()
            submissions = form_submissions_model.objects.filter(page=self.instance)
            submission_count = submissions.count()

            if not submission_count:
                return ""

            return mark_safe(
                render_to_string(
                    self.panel.template,
                    {
                        "self": self,
                        "submission_count": submission_count,
                        "last_submit_time": submissions.order_by("submit_time")
                        .last()
                        .submit_time,
                    },
                )
            )
