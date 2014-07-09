
.. _wagtailsearch_configuration:

===========================
Wagtailsearch configuration
===========================


Indexing extra fields
=====================

Fields need to be explicitly added to the search configuration in order for you to be able to search/filter on them.

You can add new fields to the search index by overriding the ``search_fields`` property and appending a list of extra ``SearchField``/``FilterField`` objects to it.

``Page`` sets a default value to ``search_fields`` indexing the ``title`` field as a ``SearchField`` and some other generally useful fields as ``FilterField``s.


Quick example
-------------

This creates an ``EventPage`` model with two fields ``description`` and ``date``. ``description`` is indexed as a ``SearchField`` and ``date`` is indexed as a ``FilterField``


.. code-block:: python

    from wagtail.wagtailsearch import indexed

    class EventPage(Page):
        description = models.TextField()
        date = models.DateField()

        search_fields = Page.search_fields + ( # Inherit search_fields from Page
            indexed.SearchField('description'),
            indexed.FilterField('date'),
        )


    # Get future events which contain the string "Christmas" in the title or description
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Christmas")


``indexed.SearchField``
-----------------------

These are added to the search index and are used for performing full-text searches on your models. These would usually be text fields.


Options
```````

 - **partial_match** (boolean) - Setting this to true allows results to be matched on parts of words. For example, this is set on the title field by default so a page titled "Hello World!" will be found if the user only types "Hel" into the search box.
 - **boost** (number) - This allows you to set fields as being more important than others. Setting this to a high number on a field will make pages with matches in that field to be ranked higher. By default, this is set to 100 on the title field and 1 on all other fields.
 - **es_extra** (dict) - This field is to allow the developer to set or override any setting on the field in the ElasticSearch mapping. Use this if you want to make use of any ElasticSearch features that are not yet supported in Wagtail.


``indexed.FilterField``
-----------------------

These are added to the search index but are not used for full-text searches. Instead, they allow you to run filters on your search results.


Indexing callables and other attributes
---------------------------------------

 .. note::

     This is not supported in the `Database Backend`_


Search/filter fields do not need to be Django fields, they could be any method or attribute on your class.

One use for this is indexing ``get_*_display`` methods Django creates automatically for fields with choices.


.. code-block:: python

    from wagtail.wagtailsearch import indexed

    class EventPage(Page):
        IS_PRIVATE_CHOICES = (
            (False, "Public"),
            (True, "Private"),
        )

        is_private = models.BooleanField(choices=IS_PRIVATE_CHOICES)

        search_fields = Page.search_fields + (
            # Index the human-readable string for searching
            indexed.SearchField('get_is_private_display'),

            # Index the boolean value for filtering
            indexed.FilterField('is_private'),
        )


Indexing non-page models
========================

Any Django model can be indexed and searched.

To do this, inherit from ``indexed.Indexed`` and add some ``search_fields`` to the model.

.. code-block:: python

    from wagtail.wagtailsearch import indexed

    class Book(models.Model, indexed.Indexed):
        title = models.CharField(max_length=255)
        genre = models.CharField(max_length=255, choices=GENRE_CHOICES)
        author = models.ForeignKey(Author)
        published_date = models.DateTimeField()

        search_fields = [
            SearchField('title', partial_match=True, boost=10),
            SearchField('get_genre_display'),

            FilterField('genre'),
            FilterField('author'),
            FilterField('published_date'),
        ]

    # As this model doesn't have a search method in its QuerySet, we have to call search directly on the backend
    >>> from wagtail.wagtailsearch.backends import get_search_backend
    >>> s = get_search_backend()

    # Run a search for a book by Roald Dahl
    >>> roald_dahl = Author.objects.get(name="Roald Dahl")
    >>> s.search("chocolate factory", Book.objects.filter(author=roald_dahl))
    [<Book: Charlie and the chocolate factory>]


Search Backends
===============

Wagtail can degrade to a database-backed text search, but we strongly recommend `Elasticsearch`_.

.. _Elasticsearch: http://www.elasticsearch.org/


Database Backend
----------------

The default DB search backend uses Django's ``__icontains`` filter.


Elasticsearch Backend
---------------------

Prerequisites are the Elasticsearch service itself and, via pip, the `elasticsearch-py`_ package:

.. code-block:: guess

  pip install elasticsearch

.. note::
  If you are using Elasticsearch < 1.0, install elasticsearch-py version 0.4.5: ```pip install elasticsearch==0.4.5```

The backend is configured in settings:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
          'URLS': ['http://localhost:9200'],
          'INDEX': 'wagtail',
          'TIMEOUT': 5,
          'FORCE_NEW': False,
      }
  }

Other than ``BACKEND`` the keys are optional and default to the values shown. ``FORCE_NEW`` is used by elasticsearch-py. In addition, any other keys are passed directly to the Elasticsearch constructor as case-sensitive keyword arguments (e.g. ``'max_retries': 1``).

If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including `Searchly`_, who offer a free account suitable for testing and development. To use Searchly:

-  Sign up for an account at `dashboard.searchly.com/users/sign\_up`_
-  Use your Searchly dashboard to create a new index, e.g. 'wagtaildemo'
-  Note the connection URL from your Searchly dashboard
-  Configure ``URLS`` and ``INDEX`` in the Elasticsearch entry in ``WAGTAILSEARCH_BACKENDS``
-  Run ``./manage.py update_index``

.. _elasticsearch-py: http://elasticsearch-py.readthedocs.org
.. _Searchly: http://www.searchly.com/
.. _dashboard.searchly.com/users/sign\_up: https://dashboard.searchly.com/users/sign_up


Rolling Your Own
----------------

Wagtail search backends implement the interface defined in ``wagtail/wagtail/wagtailsearch/backends/base.py``. At a minimum, the backend's ``search()`` method must return a collection of objects or ``model.objects.none()``. For a fully-featured search backend, examine the Elasticsearch backend code in ``elasticsearch.py``.