from wagtail.search.backends import get_search_backend


class SearchableQuerySetMixin:
    def search(
        self,
        query,
        fields=None,
        operator=None,
        order_by_relevance=True,
        partial_match=None,  # RemovedInWagtail60Warning
        backend="default",
    ):
        """
        This runs a search query on all the items in the QuerySet
        """
        search_backend = get_search_backend(backend)
        return search_backend.search(
            query,
            self,
            fields=fields,
            operator=operator,
            order_by_relevance=order_by_relevance,
            partial_match=partial_match,  # RemovedInWagtail60Warning
        )

    def autocomplete(
        self,
        query,
        fields=None,
        operator=None,
        order_by_relevance=True,
        backend="default",
    ):
        """
        This runs an autocomplete query on all the items in the QuerySet
        """
        search_backend = get_search_backend(backend)
        return search_backend.autocomplete(
            query,
            self,
            fields=fields,
            operator=operator,
            order_by_relevance=order_by_relevance,
        )
