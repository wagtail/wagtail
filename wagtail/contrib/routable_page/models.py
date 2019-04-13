from django.conf.urls import url
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import URLResolver
from django.urls.resolvers import RegexPattern

from wagtail.core.models import Page
from wagtail.core.url_routing import RouteResult


_creation_counter = 0


def route(pattern, name=None):
    def decorator(view_func):
        global _creation_counter
        _creation_counter += 1

        # Make sure page has _routablepage_routes attribute
        if not hasattr(view_func, '_routablepage_routes'):
            view_func._routablepage_routes = []

        # Add new route to view
        view_func._routablepage_routes.append((
            url(pattern, view_func, name=(name or view_func.__name__)),
            _creation_counter,
        ))

        return view_func

    return decorator


class RoutablePageMixin:
    """
    This class can be mixed in to a Page model, allowing extra routes to be
    added to it.
    """
    @route(r'^$')
    def index_route(self, request, *args, **kwargs):
        request.is_preview = getattr(request, 'is_preview', False)

        return TemplateResponse(
            request,
            self.get_template(request, *args, **kwargs),
            self.get_context(request, *args, **kwargs)
        )

    @classmethod
    def get_subpage_urls(cls):
        routes = []

        # Loop over this class's defined routes, in method resolution order.
        # Routes defined in the immediate class take precedence, followed by
        # immediate superclass and so on
        for klass in cls.__mro__:
            routes_for_class = []
            for val in klass.__dict__.values():
                if hasattr(val, '_routablepage_routes'):
                    routes_for_class.extend(val._routablepage_routes)

            # sort routes by _creation_counter so that ones earlier in the class definition
            # take precedence
            routes_for_class.sort(key=lambda route: route[1])

            routes.extend(route[0] for route in routes_for_class)

        return tuple(routes)

    @classmethod
    def get_resolver(cls):
        if '_routablepage_urlresolver' not in cls.__dict__:
            subpage_urls = cls.get_subpage_urls()
            cls._routablepage_urlresolver = URLResolver(RegexPattern(r'^/'), subpage_urls)

        return cls._routablepage_urlresolver

    def reverse_subpage(self, name, args=None, kwargs=None):
        """
        This method takes a route name/arguments and returns a URL path.
        """
        args = args or []
        kwargs = kwargs or {}

        return self.get_resolver().reverse(name, *args, **kwargs)

    def resolve_subpage(self, path):
        """
        This method takes a URL path and finds the view to call.
        """
        view, args, kwargs = self.get_resolver().resolve(path)

        # Bind the method
        view = view.__get__(self, type(self))

        return view, args, kwargs

    def route(self, request, path_components):
        """
        This hooks the subpage URLs into Wagtail's routing.
        """
        if self.live:
            try:
                path = '/'
                if path_components:
                    path += '/'.join(path_components) + '/'

                view, args, kwargs = self.resolve_subpage(path)
                return RouteResult(self, args=(view, args, kwargs))
            except Http404:
                pass

        return super().route(request, path_components)

    def serve(self, request, view=None, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if view is None:
            return super().serve(request, *args, **kwargs)
        return view(request, *args, **kwargs)

    def serve_preview(self, request, mode_name):
        view, args, kwargs = self.resolve_subpage('/')
        request.is_preview = True

        return view(request, *args, **kwargs)


class RoutablePage(RoutablePageMixin, Page):
    """
    This class extends Page by adding methods which allows extra routes to be
    added to it.
    """

    class Meta:
        abstract = True
