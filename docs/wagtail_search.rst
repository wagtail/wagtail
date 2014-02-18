Search
======

Wagtail can degrade to a database-backed text search, but we strongly recommend `Elasticsearch`_. If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including `Searchly`_, who offer a free account suitable for testing and development. To use Searchly:

-  Sign up for an account at `dashboard.searchly.com/users/sign\_up`_
-  Use your Searchly dashboard to create a new index, e.g. 'wagtaildemo'
-  Note the connection URL from your Searchly dashboard
-  Update ``WAGTAILSEARCH_ES_URLS`` and ``WAGTAILSEARCH_ES_INDEX`` in
   your local settings
-  Run ``./manage.py update_index``

.. _Elasticsearch: http://www.elasticsearch.org/
.. _Searchly: http://www.searchly.com/
.. _dashboard.searchly.com/users/sign\_up: https://dashboard.searchly.com/users/sign_up