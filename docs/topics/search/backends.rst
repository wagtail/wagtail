
.. _wagtailsearch_backends:

========
Backends
========

Wagtailsearch has support for multiple backends giving you the choice between using the database for search or an external service such as Elasticsearch.

You can configure which backend to use with the ``WAGTAILSEARCH_BACKENDS`` setting:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.db',
      }
  }


.. _wagtailsearch_backends_auto_update:

``AUTO_UPDATE``
===============

 .. versionadded:: 1.0

By default, Wagtail will automatically keep all indexes up to date. This could impact performance when editing content, especially if your index is hosted on an external service.

The ``AUTO_UPDATE`` setting allows you to disable this on a per-index basis:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': ...,
          'AUTO_UPDATE': False,
      }
  }

If you have disabled auto update, you must run the :ref:`update_index` command on a regular basis to keep the index in sync with the database.


.. _wagtailsearch_backends_atomic_rebuild:

``ATOMIC_REBUILD``
==================

.. versionadded:: 1.1

By default (when using the Elasticsearch backend), when the ``update_index`` command is run, Wagtail deletes the index and rebuilds it from scratch. This causes the search engine to not return results until the rebuild is complete and is also risky as you can't rollback if an error occurs.

Setting the ``ATOMIC_REBUILD`` setting to ``True`` makes Wagtail rebuild into a separate index while keep the old index active until the new one is fully built. When the rebuild is finished, the indexes are swapped atomically and the old index is deleted.

.. warning:: Experimental feature

    This feature is currently experimental. Please use it with caution.


``BACKEND``
===========

Here's a list of backends that Wagtail supports out of the box.

.. _wagtailsearch_backends_database:

Database Backend (default)
--------------------------

``wagtail.wagtailsearch.backends.db``

.. versionchanged:: 1.1

    Before 1.1, the full path to the backend class had to be specified: ``wagtail.wagtailsearch.backends.db.DBSearch``

The database backend is very basic and is intended only to be used in development and on small sites. It cannot order results by relevance making it not very useful when searching a large amount of pages.

It also doesn't support:

 - Searching on fields in subclasses of ``Page`` (unless the class is being searched directly)
 - :ref:`wagtailsearch_indexing_callable_fields`
 - Converting accented characters to ASCII

If any of these features are important to you, we recommend using Elasticsearch instead.


Elasticsearch Backend
---------------------

``wagtail.wagtailsearch.backends.elasticsearch``

.. versionchanged:: 1.1

    Before 1.1, the full path to the backend class had to be specified: ``wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch``

Prerequisites are the `Elasticsearch`_ service itself and, via pip, the `elasticsearch-py`_ package:

.. _Elasticsearch: https://www.elastic.co/downloads/past-releases/elasticsearch-1-7-3

.. note::

   Wagtail doesn't support Elasticsearch 2.0 yet; please use 1.x in the meantime. Elasticsearch 2.0 support is scheduled for Wagtail 1.3.

.. code-block:: sh

  pip install elasticsearch

The backend is configured in settings:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch',
          'URLS': ['http://localhost:9200'],
          'INDEX': 'wagtail',
          'TIMEOUT': 5,
      }
  }

Other than ``BACKEND`` the keys are optional and default to the values shown. In addition, any other keys are passed directly to the Elasticsearch constructor as case-sensitive keyword arguments (e.g. ``'max_retries': 1``).

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
