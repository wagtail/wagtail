
.. _wagtailsearch:

======
Search
======

Wagtail provides a comprehensive and extensible search interface. In addition, it provides ways to promote search results through "Editor's Picks." Wagtail also collects simple statistics on queries made through the search interface.

.. toctree::
    :maxdepth: 2

    indexing
    searching
    backends


Indexing
========

To make objects searchable, they firstly need to be added to the search index. This involves configuring the models/fields that you would like to index (this is done for you for Pages, Images and Documents) and then actually inserting them into the index.

See :ref:`wagtailsearch_indexing_update` for information on how to keep the objects in your search index in sync with the objects in your database.

If you have created some extra fields in a subclass of ``Page`` or ``Image``, you may want to add these new fields to the search index too so a users search query will match on their content. See :ref:`wagtailsearch_indexing_fields`.

If you have a custom model which doesn't derive from ``Page`` or ``Image`` that you would like to make searchable, see :ref:`wagtailsearch_indexing_models`.


Searching
=========

Wagtail provides an API for performing search queries on your models. You can also perform search queries on Django QuerySets.

See :ref:`wagtailsearch_searching`.


Backends
========

Wagtail provides two backends for storing the search index and performing search queries: Elasticsearch and the database. It's also possible to roll your own search backend.

See :ref:`wagtailsearch_backends`
