from wagtail.admin.views.bulk_action import BulkAction
from wagtail.contrib.forms.models import FormSubmission


class FormSubmissionBulkAction(BulkAction):
    models = [FormSubmission]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context