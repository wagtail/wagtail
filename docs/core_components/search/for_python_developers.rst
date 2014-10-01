
.. _wagtailsearch_for_python_developers:


=====================
For Python developers
=====================


Basic usage
===========

By default using the :ref:`wagtailsearch_backends_database`, Wagtail's search will only index the ``title`` field of pages. 

All searches are performed on Django QuerySets. Wagtail provides a ``search`` method on the queryset for all page models:

.. code-block:: python

    # Search future EventPages
    >>> from wagtail.wagtailcore.models import EventPage
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Hello world!")


All methods of ``PageQuerySet`` are supported by wagtailsearch:

.. code-block:: python

    # Search all live EventPages that are under the events index
    >>> EventPage.objects.live().descendant_of(events_index).search("Event")
    [<EventPage: Event 1>, <EventPage: Event 2>]


Indexing extra fields
=====================

.. versionchanged:: 0.4

    The ``indexed_fields`` configuration format was replaced with ``search_fields``

.. versionchanged:: 0.6

   The ``wagtail.wagtailsearch.indexed`` module was renamed to ``wagtail.wagtailsearch.index``


.. warning::

    Indexing extra fields is only supported with ElasticSearch as your backend. If you're using the database backend, any other fields you define via ``search_fields`` will be ignored.


Fields must be explicitly added to the ``search_fields`` property of your ``Page``-derived model, in order for you to be able to search/filter on them. This is done by overriding ``search_fields`` to append a list of extra ``SearchField``/``FilterField`` objects to it.


Example
-------------

This creates an ``EventPage`` model with two fields ``description`` and ``date``. ``description`` is indexed as a ``SearchField`` and ``date`` is indexed as a ``FilterField``


.. code-block:: python

    from wagtail.wagtailsearch import index

    class EventPage(Page):
        description = models.TextField()
        date = models.DateField()

        search_fields = Page.search_fields + ( # Inherit search_fields from Page
            index.SearchField('description'),
            index.FilterField('date'),
        )


    # Get future events which contain the string "Christmas" in the title or description
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Christmas")


``index.SearchField``
-----------------------

These are added to the search index and are used for performing full-text searches on your models. These would usually be text fields.


Options
```````

 - **partial_match** (boolean) - Setting this to true allows results to be matched on parts of words. For example, this is set on the title field by default so a page titled "Hello World!" will be found if the user only types "Hel" into the search box.
 - **boost** (number) - This allows you to set fields as being more important than others. Setting this to a high number on a field will make pages with matches in that field to be ranked higher. By default, this is set to 2 on the Page title field and 1 on all other fields.
 - **es_extra** (dict) - This field is to allow the developer to set or override any setting on the field in the ElasticSearch mapping. Use this if you want to make use of any ElasticSearch features that are not yet supported in Wagtail.


``index.FilterField``
-----------------------

These are added to the search index but are not used for full-text searches. Instead, they allow you to run filters on your search results.


Indexing callables and other attributes
---------------------------------------

 .. note::

     This is not supported in the :ref:`wagtailsearch_backends_database`


Search/filter fields do not need to be Django fields, they could be any method or attribute on your class.

One use for this is indexing ``get_*_display`` methods Django creates automatically for fields with choices.


.. code-block:: python

    from wagtail.wagtailsearch import index

    class EventPage(Page):
        IS_PRIVATE_CHOICES = (
            (False, "Public"),
            (True, "Private"),
        )

        is_private = models.BooleanField(choices=IS_PRIVATE_CHOICES)

        search_fields = Page.search_fields + (
            # Index the human-readable string for searching
            index.SearchField('get_is_private_display'),

            # Index the boolean value for filtering
            index.FilterField('is_private'),
        )


Indexing non-page models
========================

Any Django model can be indexed and searched.

To do this, inherit from ``index.Indexed`` and add some ``search_fields`` to the model.

.. code-block:: python

    from wagtail.wagtailsearch import index

    class Book(models.Model, index.Indexed):
        title = models.CharField(max_length=255)
        genre = models.CharField(max_length=255, choices=GENRE_CHOICES)
        author = models.ForeignKey(Author)
        published_date = models.DateTimeField()

        search_fields = (
            index.SearchField('title', partial_match=True, boost=10),
            index.SearchField('get_genre_display'),

            index.FilterField('genre'),
            index.FilterField('author'),
            index.FilterField('published_date'),
        )

    # As this model doesn't have a search method in its QuerySet, we have to call search directly on the backend
    >>> from wagtail.wagtailsearch.backends import get_search_backend
    >>> s = get_search_backend()

    # Run a search for a book by Roald Dahl
    >>> roald_dahl = Author.objects.get(name="Roald Dahl")
    >>> s.search("chocolate factory", Book.objects.filter(author=roald_dahl))
    [<Book: Charlie and the chocolate factory>]
