
.. _wagtailsearch_backends:

======================
Wagtailsearch backends
======================


Wagtail can degrade to a database-backed text search, but we strongly recommend `Elasticsearch`_.

.. _Elasticsearch: http://www.elasticsearch.org/


.. _wagtailsearch_backends_database:

Database Backend
===============

The default DB search backend uses Django's ``__icontains`` filter.


Elasticsearch Backend
=====================

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
================

Wagtail search backends implement the interface defined in ``wagtail/wagtail/wagtailsearch/backends/base.py``. At a minimum, the backend's ``search()`` method must return a collection of objects or ``model.objects.none()``. For a fully-featured search backend, examine the Elasticsearch backend code in ``elasticsearch.py``.