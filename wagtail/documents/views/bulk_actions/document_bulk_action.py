from django.utils.functional import cached_property

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.documents import get_document_model
from wagtail.permissions import policy_registry


class DocumentBulkAction(BulkAction):
    models = [get_document_model()]

    @cached_property
    def permission_policy(self):
        return policy_registry.get_by_type(self.model)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items_with_no_access"] = [
            {
                "item": document,
                "can_edit": self.permission_policy.user_has_permission_for_instance(
                    self.request.user, "change", document
                ),
            }
            for document in context["items_with_no_access"]
        ]
        return context
