from wagtail.admin.views.bulk_action import BulkAction
from wagtail.documents import get_document_model
from wagtail.documents.permissions import permission_policy as documents_permission_policy


class DocumentBulkAction(BulkAction):
    permission_policy = documents_permission_policy
    model = get_document_model()
    object_key = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents_with_no_access'] = [
            {
                'document': document,
                'can_edit': self.permission_policy.user_has_permission_for_instance(self.request.user, 'change', document)
            } for document in context['documents_with_no_access']
        ]
        return context
