class RouteResult(object):
    """
    An object to be returned from Page.route, which encapsulates
    all the information necessary to serve an HTTP response. Analogous to
    django.core.urlresolvers.ResolverMatch, except that it identifies
    a Page instance that we will call serve(*args, **kwargs) on, rather
    than a view function.
    """
    def __init__(self, page, view=None, args=None, kwargs=None):
        self.page = page
        self.args = args or []
        self.kwargs = kwargs or {}
        self.view = view or page.serve

    def __getitem__(self, index):
        return (self.page, self.view, self.args, self.kwargs)[index]
