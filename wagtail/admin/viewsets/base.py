class ViewSet:
    """
    Defines a viewset to be registered with the Wagtail admin.

    :param name: A name for this viewset, used as the URL namespace.
    :param url_prefix: A URL path element, given as a string, that the URLs for this viewset
        will be found under. Defaults to the same as ``name``.

    All other keyword arguments will be set as attributes on the instance.
    """

    def __init__(self, name, **kwargs):
        self.name = name
        self.url_prefix = kwargs.pop("url_prefix", self.name)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def on_register(self):
        """
        Called when the viewset is registered; subclasses can override this to perform additional setup.
        """
        pass

    def get_urlpatterns(self):
        """
        Returns a set of URL routes to be registered with the Wagtail admin.
        """
        return []

    def get_url_name(self, view_name):
        """
        Returns the namespaced URL name for the given view.
        """
        return self.name + ":" + view_name
