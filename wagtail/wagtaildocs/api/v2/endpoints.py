from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ...models import get_document_model
from .serializers import DocumentSerializer


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    default_base_serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    name = 'documents'
    model = get_document_model()
