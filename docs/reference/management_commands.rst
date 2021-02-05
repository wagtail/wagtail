.. _management_commands:

Management commands
===================


.. _publish_scheduled_pages:

publish_scheduled_pages
-----------------------

.. code-block:: console

    $ ./manage.py publish_scheduled_pages

This command publishes, updates or unpublishes pages that have had these actions scheduled by an editor. We recommend running this command once an hour.


.. _fixtree:

fixtree
-------

.. code-block:: console

    $ ./manage.py fixtree

This command scans for errors in your database and attempts to fix any issues it finds.


.. _move_pages:

move_pages
----------

.. code-block:: console

    $ manage.py move_pages from to

This command moves a selection of pages from one section of the tree to another.

Options:

- **from**
  This is the **id** of the page to move pages from. All descendants of this page will be moved to the destination. After the operation is complete, this page will have no children.

- **to**
  This is the **id** of the page to move pages to.


.. _purge_revisions:

purge_revisions
---------------

.. code-block:: console

    $ manage.py purge_revisions [--days=<number of days>]

This command deletes old page revisions which are not in moderation, live, approved to go live, or the latest
revision for a page. If the ``days`` argument is supplied, only revisions older than the specified number of
days will be deleted.


.. _update_index:

update_index
------------

.. code-block:: console

    $ ./manage.py update_index [--backend <backend name>]

This command rebuilds the search index from scratch. It is not required when using the database search backend (``wagtail.search.backends.db``).

It is recommended to run this command once a week and at the following times:

- whenever any pages have been created through a script (after an import, for example)
- whenever any changes have been made to models or search configuration

The search may not return any results while this command is running, so avoid running it at peak times.


Specifying which backend to update
``````````````````````````````````

By default, ``update_index`` will rebuild all the search indexes listed in ``WAGTAILSEARCH_BACKENDS``.

If you have multiple backends and would only like to update one of them, you can use the ``--backend`` option.

For example, to update just the default backend:

.. code-block:: console

    $ python manage.py update_index --backend default

The ``--chunk_size`` option can be used to set the size of chunks that are indexed at a time. This defaults to
1000 but may need to be reduced for larger document sizes.

Indexing the schema only
````````````````````````

You can prevent the ``update_index`` command from indexing any data by using the ``--schema-only`` option:

.. code-block:: console

    $ python manage.py update_index --schema-only


.. _wagtail_update_index:

wagtail_update_index
--------------------

An alias for the ``update_index`` command that can be used when another installed package (such as `Haystack <https://haystacksearch.org/>`_) provides a command named ``update_index``. In this case, the other package's entry in ``INSTALLED_APPS`` should appear above ``wagtail.search`` so that its ``update_index`` command takes precedence over Wagtail's.


.. _search_garbage_collect:

search_garbage_collect
----------------------

.. code-block:: console

    $ ./manage.py search_garbage_collect

Wagtail keeps a log of search queries that are popular on your website. On high traffic websites, this log may get big and you may want to clean out old search queries. This command cleans out all search query logs that are more than one week old (or a number of days configurable through the :ref:`WAGTAILSEARCH_HITS_MAX_AGE <wagtailsearch_hits_max_age>` setting).
