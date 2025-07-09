from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.functional import cached_property

from wagtail.admin.menu import WagtailMenuRegisterable, WagtailMenuRegisterableGroup


class ViewSet(WagtailMenuRegisterable):
    """
    Defines a viewset to be registered with the Wagtail admin.

    All properties of the viewset can be defined as class-level attributes, or passed as
    keyword arguments to the constructor (in which case they will override any class-level
    attributes). Additionally, the :attr:`name` property can be passed as the first positional
    argument to the constructor.

    For more information on how to use this class, see :ref:`using_base_viewset`.
    """

    #: A special value that, when passed in a kwargs dict to construct a view, indicates that
    #: the attribute should not be written and should instead be left as the view's initial value
    UNDEFINED = object()

    #: A name for this viewset, used as the default URL prefix and namespace.
    name = None

    #: The icon to use across the views.
    icon = ""

    def __init__(self, name=None, **kwargs):
        if name:
            self.__dict__["name"] = name

        for key, value in kwargs.items():
            self.__dict__[key] = value

    def get_common_view_kwargs(self, **kwargs):
        """
        Returns a dictionary of keyword arguments to be passed to all views within this viewset.
        """
        return kwargs

    def construct_view(self, view_class, **kwargs):
        """
        Wrapper for view_class.as_view() which passes the kwargs returned from get_common_view_kwargs
        in addition to any kwargs passed to this method. Items from get_common_view_kwargs will be
        filtered to only include those that are valid for the given view_class.
        """
        merged_kwargs = self.get_common_view_kwargs()
        merged_kwargs.update(kwargs)
        filtered_kwargs = {
            key: value
            for key, value in merged_kwargs.items()
            if hasattr(view_class, key) and value is not self.UNDEFINED
        }
        return view_class.as_view(**filtered_kwargs)

    def inject_view_methods(self, view_class, method_names):
        """
        Check for the presence of any of the named methods on this viewset. If any are found,
        create a subclass of view_class that overrides those methods to call the implementation
        on this viewset instead. Otherwise, return view_class unmodified.
        """
        viewset = self
        overrides = {}

        def make_view_method(viewset_method):
            def _view_method(self, *args, **kwargs):
                return viewset_method(*args, **kwargs)

            return _view_method

        for method_name in method_names:
            viewset_method = getattr(viewset, method_name, None)
            if viewset_method:
                view_method = make_view_method(viewset_method)
                view_method.__name__ = method_name
                overrides[method_name] = view_method

        if overrides:
            return type(view_class.__name__, (view_class,), overrides)
        else:
            return view_class

    @cached_property
    def url_prefix(self):
        """
        The preferred URL prefix for views within this viewset. When registered through
        Wagtail's :ref:`register_admin_viewset` hook, this will be used as the URL path component
        following ``/admin/``. Other URL registration mechanisms (e.g. editing ``urls.py`` manually)
        may disregard this and use a prefix of their own choosing.

        Defaults to the viewset's ``name``.
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

        Defaults to the viewset's ``name``.
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


class ViewSetGroup(WagtailMenuRegisterableGroup):
    """
    A container for grouping together multiple :class:`ViewSet` instances.
    Creates a menu item with a submenu for accessing the main URL for each instances.

    For more information on how to use this class, see :ref:`using_base_viewsetgroup`.
    """

    def on_register(self):
        self.register_menu_item()
