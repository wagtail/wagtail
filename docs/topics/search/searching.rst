
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

You can add a "Search" page to your site using a Django view. Here's an example that you can use:

.. code-block:: python

    # views.py

    from django.shortcuts import render
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(search_results, 10)
        try:
            search_results = paginator.page(page)
        except PageNotAnInteger:
            search_results = paginator.page(1)
        except EmptyPage:
            search_results = paginator.page(paginator.num_pages)

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

            {% if search_results.has_previous %}
                <a href="{% url 'search' %}?query={{ search_query|urlencode }}&amp;page={{ search_results.previous_page_number }}">Previous</a>
            {% endif %}

            {% if search_results.has_next %}
                <a href="{% url 'search' %}?query={{ search_query|urlencode }}&amp;page={{ search_results.next_page_number }}">Next</a>
            {% endif %}
        {% elif search_query %}
            No results found
        {% else %}
            Please type something into the search box
        {% endif %}
    {% endblock %}


.. _editors-picks:


Editor's picks
==============

Editor's picks are a way of explicitly linking relevant content to search terms, so results pages can contain curated content in addition to results from the search algorithm.

You can get a list of editors picks for a particular query using the ``Query`` class:

.. code-block:: python

    editors_picks = Query.get(search_query).editors_picks.all()


Each editors pick contains the following fields:

  ``page``
    The page object associated with the pick. Use ``{% pageurl editors_pick.page %}`` to generate a URL or provide other properties of the page object.

  ``description``
    The description entered when choosing the pick, perhaps explaining why the page is relevant to the search terms.


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
