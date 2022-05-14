from wagtail.admin.views.bulk_action import BulkAction
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.models import FormSubmission


class FormBulkAction(BulkAction):
    models = [FormSubmission]

    def get_success_message(self, num_forms, action_done):
        return _("{} form submissions have been {}d".format(num_forms, action_done))

    def get_execution_context(self):
        return {"user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
