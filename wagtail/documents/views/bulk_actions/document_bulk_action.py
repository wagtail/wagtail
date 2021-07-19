from wagtail.admin.views.bulk_action import BulkAction
from wagtail.documents import get_document_model


class DocumentBulkAction(BulkAction):
    model = get_document_model()
    object_key = 'document'
