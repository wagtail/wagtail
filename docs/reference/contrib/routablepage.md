.. _routable_page_mixin:

=====================
``RoutablePageMixin``
=====================

.. module:: wagtail.contrib.routable_page

The ``RoutablePageMixin`` mixin provides a convenient way for a page to respond on multiple sub-URLs with different views. For example, a blog section on a site might provide several different types of index page at URLs like ``/blog/2013/06/``, ``/blog/authors/bob/``, ``/blog/tagged/python/``, all served by the same page instance.

A ``Page`` using ``RoutablePageMixin`` exists within the page tree like any other page, but URL paths underneath it are checked against a list of patterns. If none of the patterns match, control is passed to subpages as usual (or failing that, a 404 error is thrown).

By default a route for ``r'^$'`` exists, which serves the content exactly like a normal ``Page`` would. It can be overridden by using ``@route(r'^$')`` on any other method of the inheriting class.


Installation
============

Add ``"wagtail.contrib.routable_page"`` to your INSTALLED_APPS:

.. code-block:: python

    INSTALLED_APPS = [
      ...

      "wagtail.contrib.routable_page",
    ]


The basics
==========

To use ``RoutablePageMixin``, you need to make your class inherit from both :class:`wagtail.contrib.routable_page.models.RoutablePageMixin` and :class:`wagtail.models.Page`, then define some view methods and decorate them with ``wagtail.contrib.routable_page.models.route``. These view methods behave like ordinary Django view functions, and must return an ``HttpResponse`` object; typically this is done through a call to ``django.shortcuts.render``.

Here's an example of an ``EventIndexPage`` with three views, assuming that an ``EventPage`` model with an ``event_date`` field has been defined elsewhere:

.. code-block:: python

    import datetime
    from django.http import JsonResponse
    from wagtail.fields import RichTextField
    from wagtail.models import Page
    from wagtail.contrib.routable_page.models import RoutablePageMixin, route


    class EventIndexPage(RoutablePageMixin, Page):

        # Routable pages can have fields like any other - here we would
        # render the intro text on a template with {{ page.intro|richtext }}
        intro = RichTextField()

        @route(r'^$') # will override the default Page serving mechanism
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

        @route(r'^past/$')
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
        @route(r'^year/(\d+)/$')
        @route(r'^year/current/$')
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

        @route(r'^year/(\d+)/count/$')
        def count_for_year(self, request, year=None):
            """
            View function that returns a simple JSON response that
            includes the number of events scheduled for a specific year
            """
            events = EventPage.objects.live().filter(event_date__year=year)

            # NOTE: The usual template/context rendering process is irrelevant
            # here, so we'll just return a HttpResponse directly
            return JsonResponse({'count': events.count()})


Rendering other pages
=====================

Another way of returning an ``HttpResponse`` is to call the ``serve`` method of another page. (Calling a page's own ``serve`` method within a view method is not valid, as the view method is already being called within ``serve``, and this would create a circular definition).

For example, ``EventIndexPage`` could be extended with a ``next/`` route that displays the page for the next event:

.. code-block:: python

    @route(r'^next/$')
    def next_event(self, request):
        """
        Display the page for the next event
        """
        future_events = EventPage.objects.live().filter(event_date__gt=datetime.date.today())
        next_event = future_events.order_by('event_date').first()

        return next_event.serve(request)


Reversing URLs
==============

:class:`~models.RoutablePageMixin` adds a :meth:`~models.RoutablePageMixin.reverse_subpage` method to your page model which you can use for reversing URLs. For example:

.. code-block:: python

    # The URL name defaults to the view method name.
    >>> event_page.reverse_subpage('events_for_year', args=(2015, ))
    'year/2015/'

This method only returns the part of the URL within the page. To get the full URL, you must append it to the values of either the :attr:`~wagtail.models.Page.url` or the :attr:`~wagtail.models.Page.full_url` attribute on your page:

.. code-block:: python

    >>> event_page.url + event_page.reverse_subpage('events_for_year', args=(2015, ))
    '/events/year/2015/'

    >>> event_page.full_url + event_page.reverse_subpage('events_for_year', args=(2015, ))
    'http://example.com/events/year/2015/'

Changing route names
--------------------

The route name defaults to the name of the view. You can override this name with the ``name`` keyword argument on ``@route``:

.. code-block:: python

    from wagtail.models import Page
    from wagtail.contrib.routable_page.models import RoutablePageMixin, route


    class EventPage(RoutablePageMixin, Page):
        ...

        @route(r'^year/(\d+)/$', name='year')
        def events_for_year(self, request, year):
            """
            View function for the events for year page
            """
            ...

.. code-block:: python

    >>> event_page.url + event_page.reverse_subpage('year', args=(2015, ))
    '/events/year/2015/'

The ``RoutablePageMixin`` class
===============================

.. automodule:: wagtail.contrib.routable_page.models
.. autoclass:: RoutablePageMixin

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


 .. _routablepageurl_template_tag:

The ``routablepageurl`` template tag
====================================

.. currentmodule:: wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags
.. autofunction:: routablepageurl

    Example:

    .. code-block:: html+django

        {% load wagtailroutablepage_tags %}

        {% routablepageurl page "feed" %}
        {% routablepageurl page "archive" 2014 08 14 %}
        {% routablepageurl page "food" foo="bar" baz="quux" %}
