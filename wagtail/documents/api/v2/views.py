from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.views import BaseAPIViewSet

from ... import get_document_model
from .serializers import DocumentSerializer


class DocumentsAPIViewSet(BaseAPIViewSet):
    base_serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ['title']
    meta_fields = BaseAPIViewSet.meta_fields + ['tags', 'download_url']
    listing_default_fields = BaseAPIViewSet.listing_default_fields + ['title', 'tags', 'download_url']
    nested_default_fields = BaseAPIViewSet.nested_default_fields + ['title', 'download_url']
    name = 'documents'
    model = get_document_model()
