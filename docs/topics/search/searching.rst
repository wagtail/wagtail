
.. _wagtailsearch_searching:


=========
Searching
=========


.. _wagtailsearch_searching_pages:

Searching QuerySets
===================

Wagtail search is built on Django's `QuerySet API <https://docs.djangoproject.com/en/1.8/ref/models/querysets/>`_. You should be able to search any Django QuerySet provided the model and the fields being filtered on have been added to the search index.


Searching Pages
---------------

Wagtail provides a shortcut for searching pages: the ``.search()`` ``QuerySet`` method. You can call this on any ``PageQuerySet``. For example:

.. code-block:: python

    # Search future EventPages
    >>> from wagtail.wagtailcore.models import EventPage
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Hello world!")


All other methods of ``PageQuerySet`` can be used with ``search()``. For example:

.. code-block:: python

    # Search all live EventPages that are under the events index
    >>> EventPage.objects.live().descendant_of(events_index).search("Event")
    [<EventPage: Event 1>, <EventPage: Event 2>]


.. note::

    The ``search()`` method will convert your ``QuerySet`` into an instance of one of Wagtail's ``SearchResults`` classes (depending on backend). This means that you must perform filtering before calling ``search()``.


.. _wagtailsearch_images_documents_custom_models:

Searching Images, Documents and custom models
---------------------------------------------

Wagtail's document and image models provide a ``search`` method on their QuerySets, just as pages do:

.. code-block:: python

    >>> from wagtail.wagtailimages.models import Image

    >>> Image.objects.filter(uploaded_by_user=user).search("Hello")
    [<Image: Hello>, <Image: Hello world!>]


:ref:`Custom models <wagtailsearch_indexing_models>` can be searched by using the ``search`` method on the search backend directly:

.. code-block:: python

    >>> from myapp.models import Book
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search books
    >>> s = get_search_backend()
    >>> s.search("Great", Book)
    [<Book: Great Expectations>, <Book: The Great Gatsby>]


You can also pass a QuerySet into the ``search`` method which allows you to add filters to your search results:

.. code-block:: python

    >>> from myapp.models import Book
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search books
    >>> s = get_search_backend()
    >>> s.search("Great", Book.objects.filter(published_date__year__lt=1900))
    [<Book: Great Expectations>]


.. _wagtailsearch_specifying_fields:

Specifying the fields to search
-------------------------------

By default, Wagtail will search all fields that have been indexed using ``index.SearchField``.

This can be limited to a certian set of fields by using the ``fields`` keyword argument:

.. code-block:: python

    # Search just the title field
    >>> EventPage.objects.search("Event", fields=["title"])
    [<EventPage: Event 1>, <EventPage: Event 2>]


Changing search behaviour
-------------------------

Search operator
^^^^^^^^^^^^^^^

The search operator specifies how search should behave when the user has typed in multiple search terms. There are two possible values:

 - "or" - The results must match at least one term (default for Elasticsearch)
 - "and" - The results must match all terms (default for database search)

Both operators have benefits and drawbacks. The "or" operator will return many more results but will likely contain a lot of results that aren't relevent. The "and" operator only returns results that contain all search terms, but require the user to be more precise with their query.

We recommend using the "or" operator when ordering by relevance and the "and" operator when ordering by anything else (note: the database backend doesn't currently support ordering by relevance).

Here's an example of using the ``operator`` keyword argument:

.. code-block:: python

    # The database contains a "Thing" model with the following items:
    # - Hello world
    # - Hello
    # - World


    # Search with the "or" operator
    >>> s = get_search_backend()
    >>> s.search("Hello world", Things, operator="or")

    # All records returned as they all contain either "hello" or "world"
    [<Thing: Hello World>, <Thing: Hello>, <Thing: World>]


    # Search with the "and" operator
    >>> s = get_search_backend()
    >>> s.search("Hello world", Things, operator="and")

    # Only "hello world" returned as that's the only item that contains both terms
    [<Thing: Hello world>]

For page, image and document models, the ``operator`` keyword argument is also supported on the QuerySet's ``search`` method:

.. code-block:: python

    >>> Page.objects.search("Hello world", operator="or")

    # All pages containing either "hello" or "world" are returned
    [<Page: Hello World>, <Page: Hello>, <Page: World>]


Custom ordering
^^^^^^^^^^^^^^^

By default, search results are ordered by relevance, if the backend supports it. To preserve the QuerySet's existing ordering, the ``order_by_relevance`` keyword argument needs to be set to ``False`` on the ``search()`` method.

For example:

.. code-block:: python

    # Get a list of events ordered by date
    >>> EventPage.objects.order_by('date').search("Event", order_by_relevance=False)

    # Events ordered by date
    [<EventPage: Easter>, <EventPage: Halloween>, <EventPage: Christmas>]


.. _wagtailsearch_annotating_results_with_score:

Annotating results with score
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each matched result, Elasticsearch calculates a "score", which is a number
that represents how relevant the result is based on the user's query. The
results are usually ordered based on the score.

There are some cases where having access to the score is useful (such as
programmatically combining two queries for different models). You can add the
score to each result by calling the ``.annotate_score(field)`` method on the
``SearchQuerySet``.

For example:

.. code-block:: python

    >>> events = EventPage.objects.search("Event").annotate_score("_score")
    >>> for event in events:
    ...    print(event.title, event._score)
    ...
    ("Easter", 2.5),
    ("Haloween", 1.7),
    ("Christmas", 1.5),

Note that the score itself is arbitrary and it is only useful for comparison
of results for the same query.

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

This functionality is provided by the :mod:`~wagtail.contrib.wagtailsearchpromotions` contrib module.
