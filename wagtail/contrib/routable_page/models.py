import logging
from functools import partial

from django.core.checks import Warning
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import URLResolver
from django.urls import path as path_func
from django.urls import re_path as re_path_func
from django.urls.resolvers import RegexPattern, RoutePattern

from wagtail.models import Page
from wagtail.url_routing import RouteResult

_creation_counter = 0

logger = logging.getLogger("wagtail.routablepage")


def _path(pattern, name=None, func=None):
    def decorator(view_func):
        global _creation_counter
        _creation_counter += 1

        # Make sure page has _routablepage_routes attribute
        if not hasattr(view_func, "_routablepage_routes"):
            view_func._routablepage_routes = []

        # Add new route to view
        view_func._routablepage_routes.append(
            (
                func(pattern, view_func, name=(name or view_func.__name__)),
                _creation_counter,
            )
        )

        return view_func

    return decorator


re_path = partial(_path, func=re_path_func)
path = partial(_path, func=path_func)

# Make route an alias of re_path for backwards compatibility.
route = re_path


class RoutablePageMixin:
    """
    This class can be mixed in to a Page model, allowing extra routes to be
    added to it.
    """

    @path("")
    def index_route(self, request, *args, **kwargs):
        request.is_preview = getattr(request, "is_preview", False)

        return TemplateResponse(
            request,
            self.get_template(request, *args, **kwargs),
            self.get_context(request, *args, **kwargs),
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
                if hasattr(val, "_routablepage_routes"):
                    routes_for_class.extend(val._routablepage_routes)

            # sort routes by _creation_counter so that ones earlier in the class definition
            # take precedence
            routes_for_class.sort(key=lambda route: route[1])

            routes.extend(route[0] for route in routes_for_class)

        return tuple(routes)

    @classmethod
    def get_resolver(cls):
        if "_routablepage_urlresolver" not in cls.__dict__:
            subpage_urls = cls.get_subpage_urls()
            cls._routablepage_urlresolver = URLResolver(
                RegexPattern(r"^/"), subpage_urls
            )

        return cls._routablepage_urlresolver

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(cls._check_path_with_regex())
        return errors

    @classmethod
    def _check_path_with_regex(cls):
        routes = cls.get_subpage_urls()
        errors = []
        for route in routes:
            if isinstance(route.pattern, RoutePattern):
                pattern = route.pattern._route
                if (
                    "(?P<" in pattern
                    or pattern.startswith("^")
                    or pattern.endswith("$")
                ):
                    errors.append(
                        Warning(
                            (
                                f"Your URL pattern {route.name or route.callback.__name__} has a "
                                "route that contains '(?P<', begins with a '^', or ends with a '$'."
                            ),
                            hint="Decorate your view with re_path if you want to use regexp.",
                            obj=cls,
                            id="wagtailroutablepage.W001",
                        )
                    )
        return errors

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
                path = "/"
                if path_components:
                    path += "/".join(path_components) + "/"

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

    def render(self, request, *args, template=None, context_overrides=None, **kwargs):
        """
        This method replicates what ``Page.serve()`` usually does when ``RoutablePageMixin``
        is not used. By default, ``Page.get_template()`` is called to derive the template
        to use for rendering, and ``Page.get_context()`` is always called to gather the
        data to be included in the context.

        You can use the ``context_overrides`` keyword argument as a shortcut to override or
        add new values to the context. For example:

        .. code-block:: python

            @path('') # override the default route
            def upcoming_events(self, request):
                return self.render(request, context_overrides={
                    'title': "Current events",
                    'events': EventPage.objects.live().future(),
                })

        You can also use the ``template`` argument to specify an alternative
        template to use for rendering. For example:

        .. code-block:: python

            @path('past/')
            def past_events(self, request):
                return self.render(
                    request,
                    context_overrides={
                        'title': "Past events",
                        'events': EventPage.objects.live().past(),
                    },
                    template="events/event_index_historical.html",
                )
        """
        if template is None:
            template = self.get_template(request, *args, **kwargs)
        context = self.get_context(request, *args, **kwargs)
        context.update(context_overrides or {})
        return TemplateResponse(request, template, context)

    def serve_preview(self, request, mode_name):
        view, args, kwargs = self.resolve_subpage("/")
        return view(request, *args, **kwargs)


class RoutablePage(RoutablePageMixin, Page):
    """
    This class extends Page by adding methods which allows extra routes to be
    added to it.
    """

    class Meta:
        abstract = True
