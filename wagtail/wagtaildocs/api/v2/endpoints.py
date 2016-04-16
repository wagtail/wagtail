from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ...models import get_document_model
from .serializers import DocumentSerializer


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags', 'download_url']
    default_fields = BaseAPIEndpoint.default_fields + ['title', 'tags', 'download_url']
    name = 'documents'
    model = get_document_model()
