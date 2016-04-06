
.. _wagtailsearch_indexing:

========
Indexing
========

To make a model searchable, you'll firstly need to add it into the search index. All pages, images and documents are indexed for you and you can start searching them right away.

If you have created some extra fields in a subclass of Page or Image, you may want to add these new fields to the search index too so that a user's search query will match on their content. See :ref:`wagtailsearch_indexing_fields` for info on how to do this.

If you have a custom model that you would like to make searchable, see :ref:`wagtailsearch_indexing_models`.


.. _wagtailsearch_indexing_update:


Updating the index
==================

If the search index is kept separate from the database (when using Elasticsearch for example), you need to keep them both in sync. There are two ways to do this: using the search signal handlers, or calling the ``update_index`` command periodically. For best speed and reliability, it's best to use both if possible.


Signal handlers
---------------

.. versionchanged:: 0.8

    Signal handlers are now automatically registered

``wagtailsearch`` provides some signal handlers which bind to the save/delete signals of all indexed models. This would automatically add and delete them from all backends you have registered in ``WAGTAILSEARCH_BACKENDS``. These signal handlers are automatically registered when the ``wagtail.wagtailsearch`` app is loaded.


The ``update_index`` command
----------------------------

Wagtail also provides a command for rebuilding the index from scratch.

:code:`./manage.py update_index`

It is recommended to run this command once a week and at the following times:

 - whenever any pages have been created through a script (after an import, for example)
 - whenever any changes have been made to models or search configuration

The search may not return any results while this command is running, so avoid running it at peak times.


.. _wagtailsearch_indexing_fields:

Indexing extra fields
=====================

.. warning::

    Indexing extra fields is only supported with ElasticSearch as your backend. If you're using the database backend, any other fields you define via ``search_fields`` will be ignored.


Fields must be explicitly added to the ``search_fields`` property of your ``Page``-derived model, in order for you to be able to search/filter on them. This is done by overriding ``search_fields`` to append a list of extra ``SearchField``/``FilterField`` objects to it.


Example
-------

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
---------------------

These are added to the search index and are used for performing full-text searches on your models. These would usually be text fields.


Options
```````

 - **partial_match** (``boolean``) - Setting this to true allows results to be matched on parts of words. For example, this is set on the title field by default so a page titled ``Hello World!`` will be found if the user only types ``Hel`` into the search box.
 - **boost** (``int/float``) - This allows you to set fields as being more important than others. Setting this to a high number on a field will make pages with matches in that field to be ranked higher. By default, this is set to 2 on the Page title field and 1 on all other fields.
 - **es_extra** (``dict``) - This field is to allow the developer to set or override any setting on the field in the ElasticSearch mapping. Use this if you want to make use of any ElasticSearch features that are not yet supported in Wagtail.


``index.FilterField``
---------------------

These are added to the search index but are not used for full-text searches. Instead, they allow you to run filters on your search results.


.. _wagtailsearch_index_relatedfields:

``index.RelatedFields``
-----------------------

This allows you to index fields from related objects. It works on all types of related fields, including their reverse accessors.

For example, if we have a book that has a ``ForeignKey`` to its author, we can nest the authors ``name`` and ``date_of_birth`` fields inside the book:

.. code-block:: python

    class Book(models.Model, indexed.Indexed):
        ...

        search_fields = [
            index.SearchField('title'),
            index.FilterField('published_date'),

            index.RelatedFields('author', [
                index.SearchField('name'),
                index.FilterField('date_of_birth'),
            ]),
        ]

This will allow you to search for books with their author's name.

It works the other way around as well, you can index an author's books allowing an author to be searched for with the titles of books they've published:

.. code-block:: python

    class Author(models.Model, indexed.Indexed):
        ...

        search_fields = [
            index.SearchField('name'),
            index.FilterField('date_of_birth'),

            index.RelatedFields('books', [
                index.SearchField('title'),
                index.FilterField('published_date'),
            ]),
        ]

.. topic:: Filtering on ``index.RelatedFields``

    It's not possible to filter on any ``index.FilterFields`` within ``index.RelatedFields`` using the ``QuerySet`` API. Although, the fields are indexed so it should be possible to use them by querying Elasticsearch manually.

    Filtering on ``index.RelatedFields`` with the ``QuerySet`` API is planned for a future release of Wagtail.

.. _wagtailsearch_indexing_callable_fields:

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

Callables also provide a way to index fields from related models. In the example from :ref:`inline_panels`, to index each BookPage by the titles of its related_links:

.. code-block:: python

    class BookPage(Page):
        # ...
        def get_related_link_titles(self):
            # Get list of titles and concatenate them
            return '\n'.join(self.related_links.all().values_list('title', flat=True))

        search_fields = Page.search_fields + [
            # ...
            index.SearchField('get_related_link_titles'),
        ]

.. _wagtailsearch_indexing_models:

Indexing custom models
======================

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
