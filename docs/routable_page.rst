====================================
Embedding URL configuration in Pages
====================================

.. versionadded:: 0.5

This document describes how to use Wagtails ``RoutablePage`` class. This class is designed for embedding URL configuration into pages.


The basics
==========

To use ``RoutablePage``. You need to make your class inherit from :class:`wagtail.contrib.wagtailroutablepage.models.RoutablePage` and configure the ``subpage_urls`` attribute with your URL configuration.

Heres a quick example of en ``EventPage`` with three views:

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

            subpage_urls = (
                url(r'^$', 'serve', name='main'),
                url(r'^archive/$', 'archive', name='archive'),
            )

    .. automethod:: resolve_subpage

        Example:

        .. code-block:: python

            view, args, kwargs = page.resolve_subpage('/past/')
            response = view(request, *args, **kwargs)

    .. automethod:: reverse_subpage

        Example:

        .. code-block:: python

            url = page.url + page.reverse_subpage('events_for_year', args=('2014', ))
