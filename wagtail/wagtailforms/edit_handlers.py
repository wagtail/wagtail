from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.edit_handlers import EditHandler


class FormSubmissionsPanel(EditHandler):
    template = "wagtailforms/edit_handlers/form_responses_panel.html"

    def render(self):
        from .models import FormSubmission
        submissions = FormSubmission.objects.filter(page=self.instance)
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
