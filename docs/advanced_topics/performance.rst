Performance
===========

Wagtail is designed for speed, both in the editor interface and on the front-end, but if you want even better performance or you need to handle very high volumes of traffic, here are some tips on eking out the most from your installation.


Editor interface
~~~~~~~~~~~~~~~~

We have tried to minimise external dependencies for a working installation of Wagtail, in order to make it as simple as possible to get going. However, a number of default settings can be configured for better performance:


Cache
-----

We recommend `Redis <http://redis.io/>`_ as a fast, persistent cache. Install Redis through your package manager (on Debian or Ubuntu: ``sudo apt-get install redis-server``), add ``django-redis`` to your ``requirements.txt``, and enable it as a cache backend:

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': '127.0.0.1:6379',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }


Search
------

Wagtail has strong support for `Elasticsearch <http://www.elasticsearch.org/>`_ - both in the editor interface and for users of your site - but can fall back to a database search if Elasticsearch isn't present. Elasticsearch is faster and more powerful than the Django ORM for text search, so we recommend installing it or using a hosted service like `Searchly <http://www.searchly.com/>`_.

For details on configuring Wagtail for Elasticsearch, see :ref:`wagtailsearch_backends_elasticsearch`.


Database
--------

Wagtail is tested on SQLite, and should work on other Django-supported database backends, but we recommend PostgreSQL for production use.


Templates
---------

The overhead from reading and compiling templates can add up. In some cases a significant performance improvement can be gained by using `Django's cached template loader <https://docs.djangoproject.com/en/1.10/ref/templates/api/#django.template.loaders.cached.Loader>`_:

.. code-block:: python

    TEMPLATES = [{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    }]

There is a caveat associated with this loader though. Changes to a template file will not be picked up once it is cached. This means that this loader should *not* be enabled during development.


Public users
~~~~~~~~~~~~

.. _caching_proxy:

Caching proxy
-------------

To support high volumes of traffic with excellent response times, we recommend a caching proxy. Both `Varnish <http://www.varnish-cache.org/>`_ and `Squid <http://www.squid-cache.org/>`_ have been tested in production. Hosted proxies like `Cloudflare <https://www.cloudflare.com/>`_ should also work well.

 Wagtail supports automatic cache invalidation for Varnish/Squid. See :ref:`frontend_cache_purging` for more information.
