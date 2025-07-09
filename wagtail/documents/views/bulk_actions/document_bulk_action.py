from wagtail.admin.views.bulk_action import BulkAction
from wagtail.documents import get_document_model
from wagtail.documents.permissions import (
    permission_policy as documents_permission_policy,
)


class DocumentBulkAction(BulkAction):
    permission_policy = documents_permission_policy
    models = [get_document_model()]

    def get_all_objects_in_listing_query(self, parent_id):
        listing_objects = self.permission_policy.instances_user_has_permission_for(
            self.request.user, "change"
        )
        if parent_id is not None:
            listing_objects = listing_objects.filter(collection_id=parent_id)

        listing_objects = listing_objects.values_list("pk", flat=True)

        if "q" in self.request.GET:
            query_string = self.request.GET.get("q", "")
            listing_objects = listing_objects.search(query_string).results()

        return listing_objects

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
