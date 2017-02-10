.. _routable_page_mixin:

=====================
``RoutablePageMixin``
=====================

.. module:: wagtail.contrib.wagtailroutablepage

The ``RoutablePageMixin`` mixin provides a convenient way for a page to respond on multiple sub-URLs with different views. For example, a blog section on a site might provide several different types of index page at URLs like ``/blog/2013/06/``, ``/blog/authors/bob/``, ``/blog/tagged/python/``, all served by the same page instance.

A ``Page`` using ``RoutablePageMixin`` exists within the page tree like any other page, but URL paths underneath it are checked against a list of patterns. If none of the patterns match, control is passed to subpages as usual (or failing that, a 404 error is thrown).


Installation
============

Add ``"wagtail.contrib.wagtailroutablepage"`` to your INSTALLED_APPS:

 .. code-block:: python

     INSTALLED_APPS = [
        ...

        "wagtail.contrib.wagtailroutablepage",
     ]


The basics
==========

To use ``RoutablePageMixin``, you need to make your class inherit from both :class:`wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin` and :class:`wagtail.wagtailcore.models.Page`, then define some view methods and decorate them with ``wagtail.contrib.wagtailroutablepage.models.route``.

Here's an example of an ``EventPage`` with three views:

.. code-block:: python

    from wagtail.wagtailcore.models import Page
    from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route


    class EventPage(RoutablePageMixin, Page):
        ...

        @route(r'^$')
        def current_events(self, request):
            """
            View function for the current events page
            """
            ...

        @route(r'^past/$')
        def past_events(self, request):
            """
            View function for the past events page
            """
            ...

        # Multiple routes!
        @route(r'^year/(\d+)/$')
        @route(r'^year/current/$')
        def events_for_year(self, request, year=None):
            """
            View function for the events for year page
            """
            ...

Reversing URLs
==============

:class:`~models.RoutablePageMixin` adds a :meth:`~models.RoutablePageMixin.reverse_subpage` method to your page model which you can use for reversing URLs. For example:

.. code-block:: python

    # The URL name defaults to the view method name.
    >>> event_page.reverse_subpage('events_for_year', args=(2015, ))
    'year/2015/'

This method only returns the part of the URL within the page. To get the full URL, you must append it to the values of either the :attr:`~wagtail.wagtailcore.models.Page.url` or the :attr:`~wagtail.wagtailcore.models.Page.full_url` attribute on your page:

.. code-block:: python

    >>> event_page.url + event_page.reverse_subpage('events_for_year', args=(2015, ))
    '/events/year/2015/'

    >>> event_page.full_url + event_page.reverse_subpage('events_for_year', args=(2015, ))
    'http://example.com/events/year/2015/'

Changing route names
--------------------

The route name defaults to the name of the view. You can override this name with the ``name`` keyword argument on ``@route``:

.. code-block:: python

    from wagtail.wagtailcore.models import Page
    from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route


    class EventPage(RoutablePageMixin, Page):
        ...

        @route(r'^year/(\d+)/$', name='year')
        def events_for_year(self, request, year):
            """
            View function for the events for year page
            """
            ...

.. code-block:: python

    >>> event_page.reverse_subpage('year', args=(2015, ))
    '/events/year/2015/'

The ``RoutablePageMixin`` class
===============================

.. automodule:: wagtail.contrib.wagtailroutablepage.models
.. autoclass:: RoutablePageMixin

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

.. currentmodule:: wagtail.contrib.wagtailroutablepage.templatetags.wagtailroutablepage_tags
.. autofunction:: routablepageurl

    Example:

    .. code-block:: html+django

        {% load wagtailroutablepage_tags %}

        {% routablepageurl page "feed" %}
        {% routablepageurl page "archive" 2014 08 14 %}
        {% routablepageurl page "food" foo="bar" baz="quux" %}
