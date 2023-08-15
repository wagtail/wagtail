from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.functional import cached_property

from wagtail.admin.menu import WagtailMenuRegisterable


class ViewSet(WagtailMenuRegisterable):
    """
    Defines a viewset to be registered with the Wagtail admin.

    All properties of the viewset can be defined as class-level attributes, or passed as
    keyword arguments to the constructor (in which case they will override any class-level
    attributes). Additionally, the `name` property can be passed as the first positional
    argument to the constructor.
    """

    #: A name for this viewset, used as the default URL prefix and namespace.
    name = None

    #: The icon to use across the views.
    icon = ""

    def __init__(self, name=None, **kwargs):
        if name:
            self.__dict__["name"] = name

        for key, value in kwargs.items():
            self.__dict__[key] = value

    @cached_property
    def url_prefix(self):
        """
        The preferred URL prefix for views within this viewset. When registered through
        Wagtail's ``register_admin_viewset`` hook, this will be used as the URL path component
        following ``/admin/``. Other URL registration mechanisms (e.g. editing urls.py manually)
        may disregard this and use a prefix of their own choosing.

        Defaults to the viewset's name.
        """
        if not self.name:
            raise ImproperlyConfigured(
                "ViewSet %r must provide a `name` property" % self
            )
        return self.name

    @cached_property
    def url_namespace(self):
        """
        The URL namespace for views within this viewset. Will be used internally as the
        application namespace for the viewset's URLs, and generally be the instance namespace
        too.

        Defaults to the viewset's name.
        """
        if not self.name:
            raise ImproperlyConfigured(
                "ViewSet %r must provide a `name` property" % self
            )
        return self.name

    def on_register(self):
        """
        Called when the viewset is registered; subclasses can override this to perform additional setup.
        """
        self.register_menu_item()

    def get_urlpatterns(self):
        """
        Returns a set of URL routes to be registered with the Wagtail admin.
        """
        return []

    def get_url_name(self, view_name):
        """
        Returns the namespaced URL name for the given view.
        """
        return self.url_namespace + ":" + view_name

    @cached_property
    def menu_icon(self):
        return self.icon

    @cached_property
    def menu_url(self):
        return reverse(self.get_url_name(self.get_urlpatterns()[0].name))
