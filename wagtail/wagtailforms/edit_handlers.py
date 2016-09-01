from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.edit_handlers import EditHandler


class BaseFormSubmissionsPanel(EditHandler):
    template = "wagtailforms/edit_handlers/form_responses_panel.html"

    def render(self):
        from .models import FormSubmission
        submissions = FormSubmission.objects.filter(page=self.instance)

        if not submissions:
            return ''

        return mark_safe(render_to_string(self.template, {
            'self': self,
            'submissions': submissions
        }))


class FormSubmissionsPanel(object):
    def __init__(self, heading=None):
        self.heading = heading

    def bind_to_model(self, model):
        heading = _('{} submissions').format(model._meta.model_name)
        return type(str('_FormResponsesPanel'), (BaseFormSubmissionsPanel,), {
            'model': model,
            'heading': self.heading or heading,
        })
