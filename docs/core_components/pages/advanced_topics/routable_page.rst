.. _routable_page:

====================================
Embedding URL configuration in Pages
====================================

.. versionadded:: 0.5

The ``RoutablePage`` class provides a convenient way for a page to respond on multiple sub-URLs with different views. For example, a blog section on a site might provide several different types of index page at URLs like ``/blog/2013/06/``, ``/blog/authors/bob/``, ``/blog/tagged/python/``, all served by the same ``BlogIndex`` page.

A ``RoutablePage`` exists within the page tree like any other page, but URL paths underneath it are checked against a list of patterns, using Django's urlconf scheme. If none of the patterns match, control is passed to subpages as usual (or failing that, a 404 error is thrown).


The basics
==========

To use ``RoutablePage``, you need to make your class inherit from :class:`wagtail.contrib.wagtailroutablepage.models.RoutablePage` and configure the ``subpage_urls`` attribute with your URL configuration.

Here's an example of an ``EventPage`` with three views:

.. code-block:: python

    from django.conf.urls import url

    from wagtail.contrib.wagtailroutablepage.models import RoutablePage


    class EventPage(RoutablePage):
        subpage_urls = (
            url(r'^$', 'current_events', name='current_events'),
            url(r'^past/$', 'past_events', name='past_events'),
            url(r'^year/(\d+)/$', 'events_for_year', name='events_for_year'),
        )

        def current_events(self, request):
            """
            View function for the current events page
            """
            ...

        def past_events(self, request):
            """
            View function for the current events page
            """
            ...

        def events_for_year(self, request):
            """
            View function for the events for year page
            """
            ...


The ``RoutablePage`` class
==========================

.. automodule:: wagtail.contrib.wagtailroutablepage.models
.. autoclass:: RoutablePage

    .. autoattribute:: subpage_urls

        Example:

        .. code-block:: python

            from django.conf.urls import url

            class MyPage(RoutablePage):
                subpage_urls = (
                    url(r'^$', 'serve', name='main'),
                    url(r'^archive/$', 'archive', name='archive'),
                )

                def serve(self, request):
                    ...

                def archive(self, request):
                    ...

    .. automethod:: resolve_subpage

        Example:

        .. code-block:: python

            view, args, kwargs = page.resolve_subpage('/past/')
            response = view(request, *args, **kwargs)

    .. automethod:: reverse_subpage

        Example:

        .. code-block:: python

            url = page.url + page.reverse_subpage('events_for_year', args=('2014', ))


 .. _routablepageurl_template_tag:

The ``routablepageurl`` template tag
====================================

.. versionadded:: 0.6

.. currentmodule:: wagtail.contrib.wagtailroutablepage.templatetags.wagtailroutablepage_tags
.. autofunction:: routablepageurl

    Example:

    .. code-block:: html+django

        {% load wagtailroutablepage_tags %}

        {% routablepageurl self "feed" %}
        {% routablepageurl self "archive" 2014 08 14 %}
        {% routablepageurl self "food" foo="bar" baz="quux" %}
