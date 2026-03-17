from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.models import CollectionViewRestriction

from ... import get_document_model
from .serializers import DocumentSerializer


class DocumentsAPIViewSet(BaseAPIViewSet):
    base_serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ["title"]
    meta_fields = BaseAPIViewSet.meta_fields + ["tags", "download_url"]
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "title",
        "tags",
        "download_url",
    ]
    nested_default_fields = BaseAPIViewSet.nested_default_fields + [
        "title",
        "download_url",
    ]
    name = "documents"
    model = get_document_model()

    def get_queryset(self):
        # Exclude documents which aren't in visible collections
        restricted_collection_ids = {
            restriction.collection_id
            for restriction in CollectionViewRestriction.objects.all()
            if not restriction.accept_request(self.request)
        }

        return super().get_queryset().exclude(collection__in=restricted_collection_ids)
