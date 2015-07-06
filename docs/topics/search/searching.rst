
.. _wagtailsearch_searching:


=========
Searching
=========


.. _wagtailsearch_searching_pages:

Searching Pages
===============

Wagtail provides a ``search`` method on the QuerySet for all page models:

.. code-block:: python

    # Search future EventPages
    >>> from wagtail.wagtailcore.models import EventPage
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Hello world!")


All methods of ``PageQuerySet`` are supported by ``wagtailsearch``:

.. code-block:: python

    # Search all live EventPages that are under the events index
    >>> EventPage.objects.live().descendant_of(events_index).search("Event")
    [<EventPage: Event 1>, <EventPage: Event 2>]


.. _wagtailsearch_frontend_views:


An example page search view
===========================

Here's an example Django view that could be used to add a "search" page to your site:

.. code-block:: python

    # views.py

    from django.shortcuts import render

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailsearch.models import Query


    def search(request):
        # Search
        search_query = request.GET.get('query', None)
        if search_query:
            search_results = Page.objects.live().search(search_query)

            # Log the query so Wagtail can suggest promoted results
            Query.get(search_query).add_hit()
        else:
            search_results = Page.objects.none()

        # Render template
        return render(request, 'search_results.html', {
            'search_query': search_query,
            'search_results': search_results,
        })


And here's a template to go with it:

.. code-block:: html

    {% extends "base.html" %}
    {% load wagtailcore_tags %}

    {% block title %}Search{% endblock %}

    {% block content %}
        <form action="{% url 'search' %}" method="get">
            <input type="text" name="query" value="{{ search_query }}">
            <input type="submit" value="Search">
        </form>

        {% if search_results %}
            <ul>
                {% for result in search_results %}
                    <li>
                        <h4><a href="{% pageurl result %}">{{ result }}</a></h4>
                        {% if result.search_description %}
                            {{ result.search_description|safe }}
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        {% elif search_query %}
            No results found
        {% else %}
            Please type something into the search box
        {% endif %}
    {% endblock %}


Promoted search results
=======================

"Promoted search results" allow editors to explicitly link relevant content to search terms, so results pages can contain curated content in addition to results from the search engine.

This functionality is provided by the :mod:`~wagtail.contrib.wagtailsearchpicks` contrib module.


Searching Images, Documents and custom models
=============================================

You can search these by using the ``search`` method on the search backend:

.. code-block:: python

    >>> from wagtail.wagtailimages.models import Image
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search images
    >>> s = get_search_backend()
    >>> s.search("Hello", Image)
    [<Image: Hello>, <Image: Hello world!>]


You can also pass a QuerySet into the ``search`` method which allows you to add filters to your search results:

.. code-block:: python

    >>> from wagtail.wagtailimages.models import Image
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search images
    >>> s = get_search_backend()
    >>> s.search("Hello", Image.objects.filter(uploaded_by_user=user))
    [<Image: Hello>]


This should work the same way for Documents and :ref:`custom models <wagtailsearch_indexing_models>` as well.
