
.. _wagtailsearch_backends:

========
Backends
========

Wagtailsearch has support for multiple backends, giving you the choice between using the database for search or an external service such as Elasticsearch. The database backend is enabled by default.

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

By default (when using the Elasticsearch backend), when the ``update_index`` command is run, Wagtail deletes the index and rebuilds it from scratch. This causes the search engine to not return results until the rebuild is complete and is also risky as you can't rollback if an error occurs.

Setting the ``ATOMIC_REBUILD`` setting to ``True`` makes Wagtail rebuild into a separate index while keep the old index active until the new one is fully built. When the rebuild is finished, the indexes are swapped atomically and the old index is deleted.

``BACKEND``
===========

Here's a list of backends that Wagtail supports out of the box.

.. _wagtailsearch_backends_database:

Database Backend (default)
--------------------------

``wagtail.wagtailsearch.backends.db``

The database backend is very basic and is intended only to be used in development and on small sites. It cannot order results by relevance, severely hampering its usefulness when searching a large collection of pages.

It also doesn't support:

 - Searching on fields in subclasses of ``Page`` (unless the class is being searched directly)
 - :ref:`wagtailsearch_indexing_callable_fields`
 - Converting accented characters to ASCII

If any of these features are important to you, we recommend using Elasticsearch instead.


.. _wagtailsearch_backends_elasticsearch:

Elasticsearch Backend
---------------------

.. versionchanged:: 1.7

    Support for Elasticsearch 2.x was added

.. versionchanged:: 1.8

    Support for Elasticsearch 5.x was added

Elasticsearch versions 1, 2 and 5 are supported. Use the appropriate backend for your version:

``wagtail.wagtailsearch.backends.elasticsearch`` (Elasticsearch 1.x)

``wagtail.wagtailsearch.backends.elasticsearch2`` (Elasticsearch 2.x)

``wagtail.wagtailsearch.backends.elasticsearch5`` (Elasticsearch 5.x)

Prerequisites are the `Elasticsearch`_ service itself and, via pip, the `elasticsearch-py`_ package. The major version of the package must match the installed version of Elasticsearch:

.. _Elasticsearch: https://www.elastic.co/downloads/elasticsearch

.. code-block:: console

  $ pip install "elasticsearch>=1.0.0,<2.0.0"  # for Elasticsearch 1.x

.. code-block:: console

  $ pip install "elasticsearch>=2.0.0,<3.0.0"  # for Elasticsearch 2.x

.. code-block:: sh

  pip install "elasticsearch>=5.0.0,<6.0.0"  # for Elasticsearch 5.x

The backend is configured in settings:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch2',
          'URLS': ['http://localhost:9200'],
          'INDEX': 'wagtail',
          'TIMEOUT': 5,
          'OPTIONS': {},
          'INDEX_SETTINGS': {},
      }
  }

Other than ``BACKEND``, the keys are optional and default to the values shown. Any defined key in ``OPTIONS`` is passed directly to the Elasticsearch constructor as case-sensitive keyword argument (e.g. ``'max_retries': 1``).

``INDEX_SETTINGS`` is a dictionary used to override the default settings to create the index. The default settings are defined inside the ``ElasticsearchSearchBackend`` class in the module ``wagtail/wagtail/wagtailsearch/backends/elasticsearch.py``. Any new key is added, any existing key, if not a dictionary, is replaced with the new value. Here's a sample on how to configure the number of shards and setting the italian LanguageAnalyzer as the default analyzer:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          ...,
          'INDEX_SETTINGS': {
              'settings': {
                  'number_of_shards': 2,
                      'index': {
                          'analysis': {
                              'analyzer': {
                                  'default': {
                                      'type': 'italian'
                                  }
                              }
                          }
                      }
                  }
              },
          }
      }

If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including `Bonsai`_, who offer a free account suitable for testing and development. To use Bonsai:

-  Sign up for an account at `Bonsai`_
-  Use your Bonsai dashboard to create a Cluster.
-  Configure ``URLS`` in the Elasticsearch entry in ``WAGTAILSEARCH_BACKENDS`` using the Cluster URL from your Bonsai dashboard
-  Run ``./manage.py update_index``

.. _elasticsearch-py: http://elasticsearch-py.readthedocs.org
.. _Bonsai: https://bonsai.io/signup


Rolling Your Own
----------------

Wagtail search backends implement the interface defined in ``wagtail/wagtail/wagtailsearch/backends/base.py``. At a minimum, the backend's ``search()`` method must return a collection of objects or ``model.objects.none()``. For a fully-featured search backend, examine the Elasticsearch backend code in ``elasticsearch.py``.
