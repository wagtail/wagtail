.. _frontend_cache_purging:

Frontend cache invalidator
==========================

.. versionchanged:: 0.7

   * Multiple backend support added
   * Cloudflare support added

.. versionchanged:: 1.7

   * Amazon CloudFront support added

Many websites use a frontend cache such as Varnish, Squid, Cloudflare or CloudFront to gain extra performance. The downside of using a frontend cache though is that they don't respond well to updating content and will often keep an old version of a page cached after it has been updated.

This document describes how to configure Wagtail to purge old versions of pages from a frontend cache whenever a page gets updated.


Setting it up
-------------

Firstly, add ``"wagtail.contrib.wagtailfrontendcache"`` to your INSTALLED_APPS:

 .. code-block:: python

     INSTALLED_APPS = [
        ...

        "wagtail.contrib.wagtailfrontendcache"
     ]

.. versionchanged:: 0.8

    Signal handlers are now automatically registered

The ``wagtailfrontendcache`` module provides a set of signal handlers which will automatically purge the cache whenever a page is published or deleted. These signal handlers are automatically registered when the ``wagtail.contrib.wagtailfrontendcache`` app is loaded.


Varnish/Squid
^^^^^^^^^^^^^

Add a new item into the ``WAGTAILFRONTENDCACHE`` setting and set the ``BACKEND`` parameter to ``wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend``. This backend requires an extra parameter ``LOCATION`` which points to where the cache is running (this must be a direct connection to the server and cannot go through another proxy).

.. code-block:: python

    # settings.py

    WAGTAILFRONTENDCACHE = {
        'varnish': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
            'LOCATION': 'http://localhost:8000',
        },
    }


Finally, make sure you have configured your frontend cache to accept PURGE requests:

 - `Varnish <https://www.varnish-cache.org/docs/3.0/tutorial/purging.html>`_
 - `Squid <http://wiki.squid-cache.org/SquidFaq/OperatingSquid#How_can_I_purge_an_object_from_my_cache.3F>`_


.. _frontendcache_cloudflare:

Cloudflare
^^^^^^^^^^

Firstly, you need to register an account with Cloudflare if you haven't already got one. You can do this here: `Cloudflare Sign up <https://www.cloudflare.com/sign-up>`_

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend``. This backend requires three extra parameters, ``EMAIL`` (your Cloudflare account email), ``TOKEN`` (your API token from Cloudflare), and ``ZONEID`` (for zone id for your domain, see below).

To find the ``ZONEID`` for your domain, read the `Cloudflare API Documentation <https://api.cloudflare.com/#getting-started-resource-ids>`_


.. code-block:: python

    # settings.py

    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend',
            'EMAIL': 'your-cloudflare-email-address@example.com',
            'TOKEN': 'your cloudflare api token',
            'ZONEID': 'your cloudflare domain zone id',
        },
    }

.. _frontendcache_aws_cloudfront:

Amazon CloudFront
^^^^^^^^^^^^^^^^^

Within Amazon Web Services you will need at least one CloudFront web distribution. If you don't have one, you can get one here: `CloudFront getting started <https://aws.amazon.com/cloudfront/>`_

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.wagtailfrontendcache.backends.CloudfrontBackend``. This backend requires one extra parameter, ``DISTRIBUTION_ID`` (your CloudFront generated distribution id).

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'cloudfront': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudfrontBackend',
            'DISTRIBUTION_ID': 'your-distribution-id',
        },
    }

Configuration of credentials can done in multiple ways. You won't need to store them in your Django settings file. You can read more about this here: `Boto 3 Docs <http://boto3.readthedocs.org/en/latest/guide/configuration.html>`_

In case you run multiple sites with Wagtail and each site has its CloudFront distribution, provide a mapping instead of a single distribution. Make sure the mapping matches with the hostnames provided in your site settings.

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'cloudfront': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudfrontBackend',
            'DISTRIBUTION_ID': {
                'www.wagtail.io': 'your-distribution-id',
                'www.madewithwagtail.org': 'your-distribution-id',
            },
        },
    }

.. note::
    In most cases, absolute URLs with ``www`` prefixed domain names should be used in your mapping. Only drop the ``www`` prefix if you're absolutely sure you're not using it (e.g. a subdomain).

Advanced usage
--------------

Invalidating more than one URL per page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Wagtail will only purge one URL per page. If your page has more than one URL to be purged, you will need to override the ``get_cached_paths`` method on your page type.

.. code-block:: python

    class BlogIndexPage(Page):
        def get_blog_items(self):
            # This returns a Django paginator of blog items in this section
            return Paginator(self.get_children().live().type(BlogPage), 10)

        def get_cached_paths(self):
            # Yield the main URL
            yield '/'

            # Yield one URL per page in the paginator to make sure all pages are purged
            for page_number in range(1, self.get_blog_items().num_pages + 1):
                yield '/?page=' + str(page_number)

Invalidating index pages
^^^^^^^^^^^^^^^^^^^^^^^^

Pages that list other pages (such as a blog index) may need to be purged as
well so any changes to a blog page is also reflected on the index (for example,
a blog post was added, deleted or its title/thumbnail was changed).

To purge these pages, we need to write a signal handler that listens for
Wagtail's ``page_published`` and ``page_unpublished`` signals for blog pages
(note, ``page_published`` is called both when a page is created and updated).
This signal handler would trigger the invalidation of the index page using the
``PurgeBatch`` class which is used to construct and dispatch invalidation requests.

.. code-block:: python

    # models.py
    from django.dispatch import receiver
    from django.db.models.signals import pre_delete

    from wagtail.wagtailcore.signals import page_published
    from wagtail.contrib.wagtailfrontendcache.utils import PurgeBatch

    ...

    def blog_page_changed(blog_page):
        # Find all the live BlogIndexPages that contain this blog_page
        batch = PurgeBatch()
        for blog_index in BlogIndexPage.objects.live():
            if blog_page in blog_index.get_blog_items().object_list:
                batch.add_page(blog_index)

        # Purge all the blog indexes we found in a single request
        batch.purge()


    @receiver(page_published, sender=BlogPage):
    def blog_published_handler(instance):
        blog_page_changed(instance)


    @receiver(pre_delete, sender=BlogPage)
    def blog_deleted_handler(instance):
        blog_page_changed(instance)


Invalidating URLs
^^^^^^^^^^^^^^^^^

The ``PurgeBatch`` class provides a ``.add_url(url)`` and a ``.add_urls(urls)``
for adding individual URLs to the purge batch.

For example, this could be useful for purging a single page on a blog index:

.. code-block:: python

    from wagtail.contrib.wagtailfrontendcache.utils import PurgeBatch

    # Purge the first page of the blog index
    batch = PurgeBatch()
    batch.add_url(blog_index.url + '?page=1')
    batch.purge()


The ``PurgeBatch`` class
^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 1.13

All of the methods available on ``PurgeBatch`` are listed below:

.. automodule:: wagtail.contrib.wagtailfrontendcache.utils
.. autoclass:: PurgeBatch

    .. automethod:: add_url

    .. automethod:: add_urls

    .. automethod:: add_page

    .. automethod:: add_pages

    .. automethod:: purge
