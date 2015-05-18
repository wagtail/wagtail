.. _routable_page_mixin:

=====================
``RoutablePageMixin``
=====================

.. module:: wagtail.contrib.wagtailroutablepage

The ``RoutablePageMixin`` mixin provides a convenient way for a page to respond on multiple sub-URLs with different views. For example, a blog section on a site might provide several different types of index page at URLs like ``/blog/2013/06/``, ``/blog/authors/bob/``, ``/blog/tagged/python/``, all served by the same page instance.

A ``Page`` using ``RoutablePageMixin`` exists within the page tree like any other page, but URL paths underneath it are checked against a list of patterns. If none of the patterns match, control is passed to subpages as usual (or failing that, a 404 error is thrown).


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

        @route(r'^year/(\d+)/$')
        def events_for_year(self, request, year):
            """
            View function for the events for year page
            """
            ...


The ``RoutablePageMixin`` class
===============================

.. automodule:: wagtail.contrib.wagtailroutablepage.models
.. autoclass:: RoutablePageMixin

    .. automethod:: get_subpage_urls

    .. automethod:: resolve_subpage

        Example:

        .. code-block:: python

            view, args, kwargs = page.resolve_subpage('/archive/')
            response = view(request, *args, **kwargs)

    .. automethod:: reverse_subpage

        Example:

        .. code-block:: python

            url = page.url + page.reverse_subpage('archive', kwargs={'year': '2014'})


 .. _routablepageurl_template_tag:

The ``routablepageurl`` template tag
====================================

.. currentmodule:: wagtail.contrib.wagtailroutablepage.templatetags.wagtailroutablepage_tags
.. autofunction:: routablepageurl

    Example:

    .. code-block:: html+django

        {% load wagtailroutablepage_tags %}

        {% routablepageurl self "feed" %}
        {% routablepageurl self "archive" 2014 08 14 %}
        {% routablepageurl self "food" foo="bar" baz="quux" %}
