from search import Search


class Searcher(object):
    def __init__(self, fields, filters=dict(), **kwargs):
        self.fields = fields
        self.filters = filters

    def __get__(self, instance, cls):
        def dosearch(query_string, **kwargs):
            search_kwargs = dict(model=cls, fields=self.fields, filters=self.filters)
            search_kwargs.update(kwargs)
            return Search().search(query_string, **search_kwargs)
        return dosearch