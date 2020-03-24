from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin.edit_handlers import EditHandler


class FormSubmissionsPanel(EditHandler):
    template = "wagtailforms/edit_handlers/form_responses_panel.html"

    def render(self):
        form_page_model = self.model
        form_submissions_model = form_page_model().get_submission_class()
        submissions = form_submissions_model.objects.filter(page=self.instance)
        submission_count = submissions.count()

        if not submission_count:
            return ''

        return mark_safe(render_to_string(self.template, {
            'self': self,
            'submission_count': submission_count,
            'last_submit_time': submissions.order_by('submit_time').last().submit_time,
        }))

    def on_model_bound(self):
        if not self.heading:
            self.heading = _('%s submissions') % self.model.get_verbose_name()
