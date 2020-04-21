.. _postgres_search:

========================
PostgreSQL search engine
========================

This contrib module provides a search engine backend using
`PostgreSQL full-text search capabilities <https://www.postgresql.org/docs/current/static/textsearch.html>`_.

.. warning::

    | You can only use this module to index data from a PostgreSQL database.

**Features**:

- It supports all the search features available in Wagtail.
- Easy to install and adds no external dependency or service.
- Excellent performance for sites with up to 200 000 pages and stays decent for sites up to a million pages.
- Faster to reindex than Elasticsearch, if you use PostgreSQL 9.5 or higher.

**Drawbacks**:

- Partial matching (``SearchField(partial_match=True)``) is not supported
- ``SearchField(boost=…)`` is only partially respected as PostgreSQL only supports four different boosts.
  So if you use five or more distinct values for the boost in your site, slight inaccuracies may occur.
- When :ref:`wagtailsearch_specifying_fields`, the index is not used,
  so it will be slow on huge sites.
- Still when :ref:`wagtailsearch_specifying_fields`, you cannot search
  on a specific method.


Installation
============

Add ``'wagtail.contrib.postgres_search',`` anywhere in your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'wagtail.contrib.postgres_search',
        ...
    ]

Then configure Wagtail to use it as a search backend.
Give it the alias `'default'` if you want it to be the default search backend:

.. code-block:: python

    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.contrib.postgres_search.backend',
        },
    }

After installing the module, run ``python manage.py migrate`` to create the necessary ``postgres_search_indexentry`` table.

You then need to index data inside this backend using
the :ref:`update_index` command. You can reuse this command whenever
you want. However, it should not be needed after a first usage since
the search engine is automatically updated when data is modified.
To disable this behaviour, see :ref:`wagtailsearch_backends_auto_update`.


Configuration
=============

Language / PostgreSQL search configuration
------------------------------------------

Use the additional ``'SEARCH_CONFIG'`` key to define which PostgreSQL
search configuration should be used. For example:

.. code-block:: python

    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.contrib.postgres_search.backend',
            'SEARCH_CONFIG': 'english',
        }
    }

As you can deduce, a PostgreSQL search configuration is mostly used to define
rules for a language, English in this case. A search configuration consists
in a compilation of algorithms (parsers & analysers)
and language specifications (stop words, stems, dictionaries, synonyms,
thesauruses, etc.).

A few search configurations are already defined by default in PostgreSQL.
You can list them using ``sudo -u postgres psql -c "\dF"`` in a Unix shell
or by using this SQL query: ``SELECT cfgname FROM pg_catalog.pg_ts_config``.

These already-defined search configurations are decent, but they’re basic
compared to commercial search engines.
If you want better support for your language, you will have to create
your own PostgreSQL search configuration. See the PostgreSQL documentation for
`an example <https://www.postgresql.org/docs/current/static/textsearch-configuration.html>`_,
`the list of parsers <https://www.postgresql.org/docs/current/static/textsearch-parsers.html>`_,
and `a guide to use dictionaries <https://www.postgresql.org/docs/current/static/textsearch-dictionaries.html>`_.

Atomic rebuild
--------------

Like the Elasticsearch backend, this backend supports
:ref:`wagtailsearch_backends_atomic_rebuild`:

.. code-block:: python

    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.contrib.postgres_search.backend',
            'ATOMIC_REBUILD': True,
        }
    }

This is nearly useless with this backend. In Elasticsearch, all data
is removed before rebuilding the index. But in this PostgreSQL backend,
only objects no longer in the database are removed. Then the index is
progressively updated, with no moment where the index is empty.

However, if you want to be extra sure that nothing wrong happens while updating
the index, you can use atomic rebuild. The index will be rebuilt, but nobody
will have access to it until reindexing is complete. If any error occurs during
the operation, all changes to the index are reverted
as if reindexing was never started.
