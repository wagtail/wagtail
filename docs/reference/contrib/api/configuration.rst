Wagtail API Configuration
=========================

Settings
--------

``WAGTAILAPI_BASE_URL`` (required when using frontend cache invalidation)

This is used in two places, when generating absolute URLs to document files and invalidating the cache.

Generating URLs to documents will fall back the the current request's hostname if this is not set. Cache invalidation cannot do this, however, so this setting must be set when using this module alongside the ``wagtailfrontendcache`` module.


``WAGTAILAPI_SEARCH_ENABLED`` (default: True)

Setting this to false will disable full text search. This applies to all endpoints.


``WAGTAILAPI_LIMIT_MAX`` (default: 20)

This allows you to change the maximum number of results a user can request at a time. This applies to all endpoints.


Adding more fields to the pages endpoint
----------------------------------------

By default, the pages endpoint only includes the ``id``, ``title`` and ``type`` fields in both the listing and detail views.

You can add more fields to the pages endpoint by setting an attribute called ``api_fields`` to a ``list`` of field names:

.. code-block:: python

    class BlogPage(Page):
        posted_by = models.CharField()
        posted_at = models.DateTimeField()
        content = RichTextField()

        api_fields = ['posted_by', 'posted_at', 'content']


This list also supports child relations (which will be nested inside the returned JSON document):

.. code-block:: python

    class BlogPageRelatedLink(Orderable):
        page = ParentalKey('BlogPage', related_name='related_links')
        link = models.URLField()

        api_fields = ['link']

    class BlogPage(Page):
        posted_by = models.CharField()
        posted_at = models.DateTimeField()
        content = RichTextField()

        api_fields = ['posted_by', 'posted_at', 'content', 'related_links']


Frontend cache invalidation
---------------------------

If you have a Varnish, Squid, Cloudflare or CloudFront instance in front of your API, the ``wagtailapi`` module can automatically invalidate cached responses for you whenever they are updated in the database.

To enable it, firstly configure the ``wagtail.contrib.wagtailfrontendcache`` module within your project (see [Wagtail frontend cache docs](http://docs.wagtail.io/en/latest/contrib_components/frontendcache.html) for more information).

Then make sure that the ``WAGTAILAPI_BASE_URL`` setting is set correctly (Example: ``WAGTAILAPI_BASE_URL = 'http://api.mysite.com'``).

Then finally, switch it on by setting ``WAGTAILAPI_USE_FRONTENDCACHE`` to ``True``.
