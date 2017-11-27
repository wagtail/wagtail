from wagtail.search.backends import get_search_backend


class SearchableQuerySetMixin:
    def search(self, query_string, fields=None,
               operator=None, order_by_relevance=True, backend='default'):
        """
        This runs a search query on all the items in the QuerySet
        """
        search_backend = get_search_backend(backend)
        return search_backend.search(query_string, self, fields=fields,
                                     operator=operator, order_by_relevance=order_by_relevance)
