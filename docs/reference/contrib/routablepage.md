(routable_page_mixin)=

# `RoutablePageMixin`

```{eval-rst}
.. module:: wagtail.contrib.routable_page
```

The `RoutablePageMixin` mixin provides a convenient way for a page to respond on multiple sub-URLs with different views. For example, a blog section on a site might provide several different types of index page at URLs like `/blog/2013/06/`, `/blog/authors/bob/`, `/blog/tagged/python/`, all served by the same page instance.

A `Page` using `RoutablePageMixin` exists within the page tree like any other page, but URL paths underneath it are checked against a list of patterns. If none of the patterns match, control is passed to subpages as usual (or failing that, a 404 error is thrown).

By default a route for `r'^$'` exists, which serves the content exactly like a normal `Page` would. It can be overridden by using `@re_path(r'^$')` or `@path('')` on any other method of the inheriting class.

## Installation

Add `"wagtail.contrib.routable_page"` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...

    "wagtail.contrib.routable_page",
]
```

## The basics

To use `RoutablePageMixin`, you need to make your class inherit from both {class}`wagtail.contrib.routable_page.models.RoutablePageMixin` and {class}`wagtail.models.Page`, then define some view methods and decorate them with `path` or `re_path`.

These view methods behave like ordinary Django view functions, and must return an `HttpResponse` object; typically this is done through a call to `django.shortcuts.render`.

The `path` and `re_path` decorators from `wagtail.contrib.routable_page.models.path` are similar to [the Django `django.urls` `path` and `re_path` functions](inv:django#topics/http/urls). The former allows the use of plain paths and converters while the latter lets you specify your URL patterns as regular expressions.

Here's an example of an `EventIndexPage` with three views, assuming that an `EventPage` model with an `event_date` field has been defined elsewhere:

```python
import datetime
from django.http import JsonResponse
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.contrib.routable_page.models import RoutablePageMixin, path, re_path


class EventIndexPage(RoutablePageMixin, Page):

    # Routable pages can have fields like any other - here we would
    # render the intro text on a template with {{ page.intro|richtext }}
    intro = RichTextField()

    @path('') # will override the default Page serving mechanism
    def current_events(self, request):
        """
        View function for the current events page
        """
        events = EventPage.objects.live().filter(event_date__gte=datetime.date.today())

        # NOTE: We can use the RoutablePageMixin.render() method to render
        # the page as normal, but with some of the context values overridden
        return self.render(request, context_overrides={
            'title': "Current events",
            'events': events,
        })

    @path('past/')
    def past_events(self, request):
        """
        View function for the past events page
        """
        events = EventPage.objects.live().filter(event_date__lt=datetime.date.today())

        # NOTE: We are overriding the template here, as well as few context values
        return self.render(
            request,
            context_overrides={
                'title': "Past events",
                'events': events,
            },
            template="events/event_index_historical.html",
        )

    # Multiple routes!
    @path('year/<int:year>/')
    @path('year/current/')
    def events_for_year(self, request, year=None):
        """
        View function for the events for year page
        """
        if year is None:
            year = datetime.date.today().year

        events = EventPage.objects.live().filter(event_date__year=year)

        return self.render(request, context_overrides={
            'title': "Events for %d" % year,
            'events': events,
        })

    @re_path(r'^year/(\d+)/count/$')
    def count_for_year(self, request, year=None):
        """
        View function that returns a simple JSON response that
        includes the number of events scheduled for a specific year
        """
        events = EventPage.objects.live().filter(event_date__year=year)

        # NOTE: The usual template/context rendering process is irrelevant
        # here, so we'll just return a HttpResponse directly
        return JsonResponse({'count': events.count()})
```

### Rendering other pages

Another way of returning an `HttpResponse` is to call the `serve` method of another page. (Calling a page's own `serve` method within a view method is not valid, as the view method is already being called within `serve`, and this would create a circular definition).

For example, `EventIndexPage` could be extended with a `next/` route that displays the page for the next event:

```python
@path('next/')
def next_event(self, request):
    """
    Display the page for the next event
    """
    future_events = EventPage.objects.live().filter(event_date__gt=datetime.date.today())
    next_event = future_events.order_by('event_date').first()

    return next_event.serve(request)
```

### Reversing URLs

{class}`~models.RoutablePageMixin` adds a {meth}`~models.RoutablePageMixin.reverse_subpage` method to your page model which you can use for reversing URLs. For example:

```python
    # The URL name defaults to the view method name.
    >>> event_page.reverse_subpage('events_for_year', args=(2015, ))
    'year/2015/'
```

This method only returns the part of the URL within the page. To get the full URL, you must append it to the values of either the {meth}`~wagtail.models.Page.get_url` method or the {attr}`~wagtail.models.Page.full_url` attribute on your page:

```python
>>> event_page.get_url() + event_page.reverse_subpage('events_for_year', args=(2015, ))
'/events/year/2015/'

>>> event_page.full_url + event_page.reverse_subpage('events_for_year', args=(2015, ))
'http://example.com/events/year/2015/'
```

### Changing route names

The route name defaults to the name of the view. You can override this name with the `name` keyword argument on `@path` or `re_path`:

```python
from wagtail.models import Page
from wagtail.contrib.routable_page.models import RoutablePageMixin, re_path


class EventPage(RoutablePageMixin, Page):
    ...

    @re_path(r'^year/(\d+)/$', name='year')
    def events_for_year(self, request, year):
        """
        View function for the events for year page
        """
        ...
```

```python
>>> event_page.url + event_page.reverse_subpage('year', args=(2015, ))
'/events/year/2015/'
```

## The `RoutablePageMixin` class

```{eval-rst}
.. automodule:: wagtail.contrib.routable_page.models
.. autoclass:: RoutablePageMixin

  .. automethod:: route

    This method overrides the default :meth:`Page.route() <wagtail.models.Page.route>`
    method to route requests to the appropriate view method.

    It sets ``routable_resolver_match`` on the request object to make sub-URL routing
    information available downstream in the same way that Django sets
    :attr:`request.resolver_match <django.http.HttpRequest.resolver_match>`.

  .. automethod:: render

  .. automethod:: get_subpage_urls

  .. automethod:: resolve_subpage

    Example:

    .. code-block:: python

        view, args, kwargs = page.resolve_subpage('/past/')
        response = view(request, *args, **kwargs)

  .. automethod:: reverse_subpage

    Example:

    .. code-block:: python

        url = page.url + page.reverse_subpage('events_for_year', kwargs={'year': '2014'})
```

(routablepageurl_template_tag)=

## The `routablepageurl` template tag

```{eval-rst}
.. currentmodule:: wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags
.. autofunction:: routablepageurl

```

Example:

```html+django
{% load wagtailroutablepage_tags %}

{% routablepageurl page "feed" %}
{% routablepageurl page "archive" 2014 08 14 %}
{% routablepageurl page "food" foo="bar" baz="quux" %}
```
