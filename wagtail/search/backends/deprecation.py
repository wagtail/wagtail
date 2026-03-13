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


class AsciiFoldingMixin:
    """
    Mixin for Elasticsearch backends to make ASCII folding configurable.
    
    By default, ASCII folding is enabled for backward compatibility, which
    converts special characters (ä, ö, ü) to ASCII equivalents (a, o, u).
    
    Set ascii_folding=False in OPTIONS to disable this behavior:
    
        WAGTAILSEARCH_BACKENDS = {
            "default": {
                "BACKEND": "wagtail.search.backends.elasticsearch7",
                "OPTIONS": {
                    "ascii_folding": False
                }
            }
        }
    """
    
    def __init__(self, params):
        super().__init__(params)
        # Get ascii_folding option from OPTIONS, default to True for backward compatibility
        self.ascii_folding = params.get("OPTIONS", {}).get("ascii_folding", True)
    
    def get_index_settings(self):
        """Override to conditionally add ASCII folding filters"""
        settings = super().get_index_settings()
        
        if not self.ascii_folding:
            # Remove asciifolding from all analyzers
            analyzers = settings.get("settings", {}).get("analysis", {}).get("analyzer", {})
            
            for analyzer_name, analyzer_config in analyzers.items():
                if "filter" in analyzer_config and isinstance(analyzer_config["filter"], list):
                    # Remove asciifolding from the filter list
                    analyzer_config["filter"] = [
                        f for f in analyzer_config["filter"] if f != "asciifolding"
                    ]
        
        return settings
