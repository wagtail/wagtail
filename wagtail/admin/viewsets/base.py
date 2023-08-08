from django.core.exceptions import ImproperlyConfigured


class ViewSet:
    """
    Defines a viewset to be registered with the Wagtail admin.

    :param name: A name for this viewset, used as the URL namespace. Alternatively, the :attr:`admin_url_namespace` attribute or :meth:`get_admin_url_namespace` method can be used to define the URL namespace on the class.
    :param url_prefix: A URL path element, given as a string, that the URLs for this viewset
        will be found under. Defaults to the same as ``name``. Alternatively, the :attr:`base_url_path` attribute or :meth:`get_admin_base_path` method can be used to define the URL path on the class.

    All other keyword arguments will be set as attributes on the instance.
    """

    #: The URL namespace to use for the admin views.
    admin_url_namespace = ""

    #: The base URL path to use for the admin views.
    base_url_path = ""

    def __init__(self, name=None, **kwargs):
        self.name = name or self.get_admin_url_namespace()
        if not self.name:
            raise ImproperlyConfigured(
                "Instances of wagtail.admin.viewsets.base.ViewSet must provide "
                "a name for the viewset, an admin_url_namespace attribute, or "
                "a get_admin_url_namespace() method"
            )

        self.url_prefix = kwargs.pop("url_prefix", self.get_admin_base_path())
        if not self.url_prefix:
            self.url_prefix = self.name

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_admin_url_namespace(self):
        """Returns the URL namespace for the admin URLs for this viewset."""
        if not self.admin_url_namespace:
            return None
        return self.admin_url_namespace

    def get_admin_base_path(self):
        """
        Returns the base path for the admin URLs for this viewset.
        The returned string must not begin or end with a slash.
        """
        if not self.base_url_path:
            return None
        return self.base_url_path.strip().strip("/")

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
