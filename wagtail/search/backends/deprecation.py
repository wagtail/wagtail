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
