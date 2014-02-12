from wagtail.wagtailsearch.backends import get_search_backend


class Searcher(object):
    def __init__(self, fields, filters=dict(), **kwargs):
        self.fields = fields
        self.filters = filters

    def __get__(self, instance, cls):
        def dosearch(query_string, **kwargs):
            # Get backend
            if 'backend' in kwargs:
                backend = kwargs['backend']
                del kwargs['backend']
            else:
                backend = 'default'

            # Build search kwargs
            search_kwargs = dict(model=cls, fields=self.fields, filters=self.filters)
            search_kwargs.update(kwargs)

            # Run search
            return get_search_backend(backend=backend).search(query_string, **search_kwargs)
        return dosearch
