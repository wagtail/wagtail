from pydoc import doc
from wagtail.admin.views.bulk_action import BulkAction
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.models import FormSubmission
from wagtail.models import Page


class FormSubmissionBulkAction(BulkAction):
    models = [FormSubmission]
    form_page = None

    def get_success_message(self, num_forms, action_done):
        return _("{} form submissions have been {}d".format(num_forms, action_done))

    def get_execution_context(self):
        return {"user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.form_page = kwargs.get("form_page")
        data_headings = []
        for name in context["items"][0]["item"].form_data:
            data_headings.append(
                {
                    "name": name.replace("_", " ").title(),
                }
            )
        context.update(
            {
                "data_headings": data_headings,
                "app_label": "wagtailforms",
                "model_name": "formsubmission",
            }
        )
        return context
