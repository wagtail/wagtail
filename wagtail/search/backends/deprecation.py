import warnings

from wagtail.utils.deprecation import RemovedInWagtail80Warning


class IndexOptionMixin:
    """
    Mixin for search backends to recognise the deprecated INDEX option in the
    search config
    """

    def __init__(self, params):
        if "INDEX" in params:
            warnings.warn(
                "The INDEX option on Elasticsearch / OpenSearch backends is deprecated. "
                "Please use the INDEX_PREFIX option instead.",
                category=RemovedInWagtail80Warning,
            )
            index_name = params.pop("INDEX")
            if "INDEX_PREFIX" not in params:
                params["INDEX_PREFIX"] = f"{index_name}_"

        super().__init__(params)


# RemovedInWagtail80Warning
class LegacyContentTypeMatchMixin:
    """
    Mixin for query compilers to match content type on either the legacy 'content_type' field
    or the current '_django_content_type' field
    """

    def get_content_type_filter(self):
        # Query content_type using a "match" query. See comment in
        # ElasticsearchBaseMapping.get_document for more details
        content_type = self.mapping_class(self.queryset.model).get_content_type()

        return {
            "bool": {
                "should": [
                    {"match": {"_django_content_type": content_type}},
                    {"match": {"content_type": content_type}},
                ]
            }
        }
